"""
Pure algorithmic analysis functions — no LLM, no async, no state dict.
Called directly from analyze_node in analysis_builder.py.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import combinations
from typing import Any

from app.models.schemas import (
    Anomaly,
    CascadeChain,
    FocusTimeScore,
    Intervention,
    Meeting,
    MeetingClassification,
    MeetingEdge,
    MeetingHealth,
    NetworkGraph,
    PersonNode,
    Recommendation,
    ROIProjection,
    WasteScore,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Classification
# ============================================================================

def classify_meetings(meetings: list[Meeting]) -> list[MeetingClassification]:
    """Heuristic classification — no LLM."""
    results: list[MeetingClassification] = []

    for meeting in meetings:
        title_lower = (meeting.title or "").lower()
        notes_lower = (meeting.notes_text or "").lower()
        attendee_count = len(meeting.attendee_emails)

        meeting_type: str
        confidence: float

        # --- rule set (first match wins) ---
        if attendee_count == 2 or any(k in title_lower for k in ("1:1", "one on one", "1-1", "one-on-one")):
            meeting_type, confidence = "1:1", 0.95

        elif any(k in title_lower for k in ("standup", "stand-up", "daily", "scrum", "huddle")) and attendee_count > 2:
            meeting_type, confidence = "standup", 0.93

        elif any(k in title_lower for k in ("planning", "sprint plan", "roadmap", "backlog")):
            meeting_type, confidence = "planning", 0.90

        elif any(k in title_lower for k in ("review", "retro", "retrospective", "decision", "approval", "go/no-go")):
            meeting_type, confidence = "decision", 0.88

        elif any(k in title_lower for k in ("brainstorm", "ideation", "workshop")):
            meeting_type, confidence = "brainstorm", 0.87

        elif any(k in title_lower for k in ("social", "lunch", "coffee", "happy hour", "offsite")):
            meeting_type, confidence = "social", 0.92

        elif any(k in title_lower for k in ("status", "update", "report", "weekly", "monthly", "all hands", "all-hands", "vendor", "demo")):
            meeting_type, confidence = "status-update", 0.80

        else:
            # Check notes for decision-like language
            if any(k in notes_lower for k in ("decided", "approved", "agreed", "action:")):
                meeting_type, confidence = "decision", 0.70
            else:
                meeting_type, confidence = "status-update", 0.50

        results.append(
            MeetingClassification(
                meeting_id=meeting.meeting_id,
                meeting_type=meeting_type,  # type: ignore[arg-type]
                confidence=confidence,
            )
        )

    return results


# ============================================================================
# Cost computation
# ============================================================================

def compute_costs(meetings: list[Meeting], hourly_rate: float) -> dict[str, float]:
    """meeting_id (str) → dollar cost.  Formula: (duration_min/60) * attendees * rate."""
    costs: dict[str, float] = {}
    for meeting in meetings:
        cost = (meeting.duration_minutes / 60.0) * len(meeting.attendee_emails) * hourly_rate
        costs[str(meeting.meeting_id)] = round(cost, 2)
    return costs


# ============================================================================
# Participation analysis
# ============================================================================

# Ideal attendee counts by type (used for optional_ratio estimation)
_TYPE_NORMS: dict[str, int] = {
    "1:1": 2,
    "standup": 6,
    "planning": 8,
    "decision": 5,
    "brainstorm": 6,
    "social": 10,
    "status-update": 8,
}


def analyze_participation(
    meetings: list[Meeting],
    classifications: list[MeetingClassification] | None = None,
) -> dict[str, dict]:
    """meeting_id (str) → {optional_ratio, organizer_recurrence_count}."""
    # Build classification lookup
    class_map: dict[str, str] = {}
    if classifications:
        for mc in classifications:
            class_map[str(mc.meeting_id)] = mc.meeting_type

    # Count how often each organizer appears
    organizer_counts: dict[str, int] = defaultdict(int)
    for meeting in meetings:
        if meeting.organizer_email:
            organizer_counts[str(meeting.organizer_email)] += 1

    result: dict[str, dict] = {}
    for meeting in meetings:
        mid = str(meeting.meeting_id)
        meeting_type = class_map.get(mid, "status-update")
        norm = _TYPE_NORMS.get(meeting_type, 8)
        actual = len(meeting.attendee_emails)

        # Estimate optional ratio based on over-attendance relative to norm
        if actual <= norm:
            optional_ratio = 0.0
        elif actual <= norm * 1.5:
            optional_ratio = 0.25
        elif actual <= norm * 2:
            optional_ratio = 0.50
        else:
            optional_ratio = 0.75

        org_count = 0
        if meeting.organizer_email:
            org_count = organizer_counts[str(meeting.organizer_email)]

        result[mid] = {
            "optional_ratio": optional_ratio,
            "organizer_recurrence_count": org_count,
        }

    return result


# ============================================================================
# Recurrence analysis
# ============================================================================

def analyze_recurrence(meetings: list[Meeting]) -> dict[str, dict]:
    """meeting_id (str) → {staleness_score, attendance_drop_percentage}."""
    # Group by (title, organizer) to detect series
    series: dict[tuple, list[Meeting]] = defaultdict(list)
    for meeting in meetings:
        key = (meeting.title.lower().strip(), str(meeting.organizer_email or ""))
        series[key].append(meeting)

    result: dict[str, dict] = {}

    for meeting in meetings:
        mid = str(meeting.meeting_id)
        key = (meeting.title.lower().strip(), str(meeting.organizer_email or ""))
        group = series[key]

        staleness_score = 0.0
        attendance_drop = 0.0

        if len(group) > 1:
            # Sort chronologically
            group_sorted = sorted(group, key=lambda m: m.start_datetime)
            earliest = group_sorted[0].start_datetime
            latest = group_sorted[-1].start_datetime
            age_days = (latest - earliest).days

            # Age bonus
            if age_days > 180:
                staleness_score += 0.4

            # Attendance drop: compare first and last third
            third = max(1, len(group_sorted) // 3)
            early_avg = sum(len(m.attendee_emails) for m in group_sorted[:third]) / third
            late_avg = sum(len(m.attendee_emails) for m in group_sorted[-third:]) / third

            if early_avg > 0:
                drop = (early_avg - late_avg) / early_avg
                attendance_drop = max(0.0, drop)
                staleness_score += min(0.6, drop * 0.6)

            staleness_score = min(1.0, staleness_score)

        result[mid] = {
            "staleness_score": round(staleness_score, 3),
            "attendance_drop_percentage": round(attendance_drop * 100, 1),
        }

    return result


# ============================================================================
# Waste scoring
# ============================================================================

def compute_waste_scores(
    meetings: list[Meeting],
    classifications: list[MeetingClassification],
    costs: dict[str, float],
    decisions: dict[str, list[str]],
    participation: dict[str, dict],
    recurrence: dict[str, dict],
    config: dict[str, Any],
) -> list[WasteScore]:
    """Weighted composite waste score per meeting."""
    from app.config import settings  # local to avoid circular at module load

    cost_weight = float(config.get("cost_weight", settings.WEIGHT_COST))
    decision_weight = float(config.get("decision_deficit_weight", settings.WEIGHT_DECISION))
    participation_weight = float(config.get("participation_weight", settings.WEIGHT_PARTICIPATION))
    recurrence_weight = float(config.get("recurrence_weight", settings.WEIGHT_RECURRENCE))

    # Build classification lookup
    class_map: dict[str, str] = {str(mc.meeting_id): mc.meeting_type for mc in classifications}

    # Normalise costs (0-1 relative to max)
    if costs:
        max_cost = max(costs.values()) or 1.0
    else:
        max_cost = 1.0

    results: list[WasteScore] = []

    for meeting in meetings:
        mid = str(meeting.meeting_id)
        meeting_type = class_map.get(mid, "status-update")

        # --- cost_factor ---
        cost_factor = min(1.0, costs.get(mid, 0.0) / max_cost)

        # --- decision_deficit ---
        meeting_decisions = decisions.get(mid, [])
        num_decisions = len(meeting_decisions)
        decision_deficit = max(0.0, 1.0 - num_decisions * 0.33)

        # Stack reductions for each positive decision keyword found in notes
        notes_lower = (meeting.notes_text or "").lower()
        positive_count = sum(
            1 for k in ("decided", "approved", "agreed", "action:")
            if k in notes_lower
        )
        if positive_count:
            decision_deficit = max(0.0, decision_deficit - 0.40 * min(positive_count, 3))
        # Increase if notes suggest a wasted meeting
        if any(k in notes_lower for k in ("no decision", "status update", "could have been email", "no decision reached")):
            decision_deficit = min(1.0, decision_deficit + 0.20)

        # --- participation_imbalance ---
        part = participation.get(mid, {})
        opt_ratio = part.get("optional_ratio", 0.0)
        norm = _TYPE_NORMS.get(meeting_type, 8)
        actual = len(meeting.attendee_emails)
        over_attended = actual > norm * 2
        if over_attended:
            participation_imbalance = min(1.0, opt_ratio + 0.30)
        else:
            participation_imbalance = opt_ratio

        # --- recurrence_staleness ---
        rec = recurrence.get(mid, {})
        recurrence_staleness = rec.get("staleness_score", 0.0)

        # --- composite ---
        composite = (
            cost_factor * cost_weight
            + decision_deficit * decision_weight
            + participation_imbalance * participation_weight
            + recurrence_staleness * recurrence_weight
        )
        composite = min(1.0, round(composite, 4))

        # --- category ---
        if composite >= 0.50:
            category = "High Waste"
        elif composite >= 0.30:
            category = "Medium Waste"
        elif composite >= 0.15:
            category = "Low Waste"
        else:
            category = "High Value"

        results.append(
            WasteScore(
                meeting_id=meeting.meeting_id,
                cost_factor=round(cost_factor, 4),
                decision_deficit=round(decision_deficit, 4),
                participation_imbalance=round(participation_imbalance, 4),
                recurrence_staleness=round(recurrence_staleness, 4),
                composite_score=composite,
                category=category,  # type: ignore[arg-type]
                threshold_exceeded=composite >= 0.50,
            )
        )

    return results


# ============================================================================
# Focus time scores
# ============================================================================

_WORK_START_HOUR = 9
_WORK_END_HOUR = 18
_FOCUS_BLOCK_MINUTES = 90  # 90-minute block needed to count as "focus time"


def compute_focus_scores(meetings: list[Meeting]) -> list[FocusTimeScore]:
    """Per-person: total meeting hours, focus blocks, focus_percentage."""
    # Build per-person calendar of (start, end) pairs
    person_calendar: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    for meeting in meetings:
        for email in meeting.attendee_emails:
            person_calendar[str(email)].append(
                (meeting.start_datetime, meeting.end_datetime)
            )

    results: list[FocusTimeScore] = []

    for person_email, slots in person_calendar.items():
        # Total meeting minutes
        total_meeting_minutes = sum(
            int((end - start).total_seconds() / 60) for start, end in slots
        )
        total_meeting_hours = round(total_meeting_minutes / 60.0, 2)

        # Estimate available work minutes across all days with meetings
        days_with_meetings: set[str] = set()
        for start, _ in slots:
            days_with_meetings.add(start.strftime("%Y-%m-%d"))

        work_minutes_per_day = (_WORK_END_HOUR - _WORK_START_HOUR) * 60
        total_work_minutes = len(days_with_meetings) * work_minutes_per_day

        # For each day, sort meetings and find 2h+ gaps in working hours
        focus_blocks = 0
        longest_focus = 0

        by_day: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
        for start, end in slots:
            by_day[start.strftime("%Y-%m-%d")].append((start, end))

        for day_str, day_slots in by_day.items():
            day_date = datetime.strptime(day_str, "%Y-%m-%d")
            day_start = day_date.replace(hour=_WORK_START_HOUR, minute=0, second=0)
            day_end = day_date.replace(hour=_WORK_END_HOUR, minute=0, second=0)

            sorted_slots = sorted(day_slots, key=lambda t: t[0])

            # Find gaps between meetings (and before first / after last)
            boundaries = [day_start] + [end for _, end in sorted_slots] + [day_end]
            starts = [start for start, _ in sorted_slots] + [day_end]

            for gap_start, gap_end in zip(boundaries, starts):
                gap_start = max(gap_start, day_start)
                gap_end = min(gap_end, day_end)
                gap_minutes = int((gap_end - gap_start).total_seconds() / 60)
                if gap_minutes >= _FOCUS_BLOCK_MINUTES:
                    focus_blocks += 1
                    longest_focus = max(longest_focus, gap_minutes)

        # focus_percentage: free working time / total working time
        if total_work_minutes > 0:
            focus_percentage = max(0.0, 1.0 - (total_meeting_minutes / total_work_minutes))
        else:
            focus_percentage = 1.0

        results.append(
            FocusTimeScore(
                person_email=person_email,
                total_meeting_hours=total_meeting_hours,
                focus_blocks_remaining=focus_blocks,
                longest_focus_block_minutes=longest_focus,
                focus_percentage=round(min(1.0, focus_percentage), 4),
            )
        )

    return results


# ============================================================================
# Meeting health scores
# ============================================================================

_DURATION_RANGES: dict[str, tuple[int, int]] = {
    "standup": (5, 30),
    "1:1": (20, 60),
    "planning": (45, 180),
    "decision": (30, 90),
    "brainstorm": (30, 90),
    "social": (30, 180),
    "status-update": (15, 120),
}

_ATTENDEE_IDEAL: dict[str, tuple[int, int]] = {
    "standup": (3, 10),
    "1:1": (2, 2),
    "planning": (4, 10),
    "decision": (3, 7),
    "brainstorm": (4, 8),
    "social": (3, 20),
    "status-update": (3, 12),
}


def compute_health_scores(
    meetings: list[Meeting],
    classifications: list[MeetingClassification],
) -> list[MeetingHealth]:
    """Rules-based health scoring."""
    class_map = {str(mc.meeting_id): mc.meeting_type for mc in classifications}

    results: list[MeetingHealth] = []

    for meeting in meetings:
        mid = str(meeting.meeting_id)
        meeting_type = class_map.get(mid, "status-update")
        notes = meeting.notes_text or ""

        # has_agenda: notes longer than 30 chars
        has_agenda = len(notes.strip()) > 30

        # duration_appropriate
        dur_min, dur_max = _DURATION_RANGES.get(meeting_type, (15, 120))
        duration_appropriate = dur_min <= meeting.duration_minutes <= dur_max

        # attendee_fit_score
        att_min, att_max = _ATTENDEE_IDEAL.get(meeting_type, (3, 12))
        actual = len(meeting.attendee_emails)
        if att_min <= actual <= att_max:
            attendee_fit_score = 1.0
        elif actual < att_min:
            # Under-attended: slight penalty
            attendee_fit_score = max(0.0, 1.0 - (att_min - actual) * 0.1)
        else:
            # Over-attended: steeper penalty
            attendee_fit_score = max(0.0, 1.0 - (actual - att_max) * 0.08)

        # overall_health_score: weighted combo
        agenda_score = 0.5 if has_agenda else 0.0
        duration_score = 0.3 if duration_appropriate else 0.0
        fit_score = attendee_fit_score * 0.2
        overall = agenda_score + duration_score + fit_score

        # Bonus for structured notes
        notes_lower = notes.lower()
        if any(k in notes_lower for k in ("decision:", "action:", "decided", "agreed")):
            overall = min(1.0, overall + 0.1)

        results.append(
            MeetingHealth(
                meeting_id=meeting.meeting_id,
                has_agenda=has_agenda,
                duration_appropriate=duration_appropriate,
                attendee_fit_score=round(attendee_fit_score, 4),
                overall_health_score=round(overall, 4),
            )
        )

    return results


# ============================================================================
# Cascade chains and anomalies
# ============================================================================

def detect_cascades_anomalies(
    meetings: list[Meeting],
    waste_scores: list[WasteScore],
    costs: dict[str, float],
    focus_scores: list[FocusTimeScore] | None = None,
) -> tuple[list[CascadeChain], list[Anomaly]]:
    """Detect cascade meeting chains and structural anomalies."""
    # Build lookup maps
    waste_map: dict[str, WasteScore] = {str(ws.meeting_id): ws for ws in waste_scores}

    # --- Cascade detection ---
    # High decision_deficit meetings (>0.8) that have follow-up meetings
    # within 72 hours with >40% attendee overlap
    cascades: list[CascadeChain] = []
    processed_origins: set[str] = set()

    sorted_meetings = sorted(meetings, key=lambda m: m.start_datetime)

    for i, origin in enumerate(sorted_meetings):
        origin_id = str(origin.meeting_id)
        ws = waste_map.get(origin_id)
        if not ws or ws.decision_deficit <= 0.8:
            continue
        if origin_id in processed_origins:
            continue
        # Skip standups and 1:1s — they are always short/small by design
        if origin.duration_minutes < 20 or len(origin.attendee_emails) <= 2:
            continue

        origin_attendees = set(str(e) for e in origin.attendee_emails)
        spawned_ids: list = []
        chain_cost = costs.get(origin_id, 0.0)

        # Look for follow-up meetings within 72 hours
        cutoff = origin.end_datetime + timedelta(hours=72)
        for other in sorted_meetings[i + 1:]:
            if other.start_datetime > cutoff:
                break
            other_attendees = set(str(e) for e in other.attendee_emails)
            if not origin_attendees or not other_attendees:
                continue
            overlap = len(origin_attendees & other_attendees) / len(origin_attendees)
            if overlap > 0.40:
                spawned_ids.append(other.meeting_id)
                chain_cost += costs.get(str(other.meeting_id), 0.0)

        if spawned_ids:
            processed_origins.add(origin_id)
            cascades.append(
                CascadeChain(
                    origin_meeting_id=origin.meeting_id,
                    spawned_meeting_ids=spawned_ids,
                    total_cascade_cost=round(chain_cost, 2),
                    cascade_depth=len(spawned_ids),
                )
            )

    # --- Anomaly detection ---
    anomalies: list[Anomaly] = []

    # Person overload: flag anyone with more than 15 hours of meetings in the period
    if focus_scores:
        for fs in focus_scores:
            if fs.total_meeting_hours > 15:
                anomalies.append(
                    Anomaly(
                        entity_id=fs.person_email,
                        entity_type="person",
                        anomaly_type="meeting_overload",
                        severity="high",
                        description=(
                            f"{fs.person_email} has {fs.total_meeting_hours:.1f} hours of meetings "
                            f"in this period ({fs.total_meeting_hours / 3:.1f}h/week average). "
                            f"Only {(fs.focus_percentage * 100):.0f}% of working time is meeting-free."
                        ),
                    )
                )

    # Oversized standup anomaly
    for meeting in meetings:
        mid = str(meeting.meeting_id)
        ws = waste_map.get(mid)
        if ws and len(meeting.attendee_emails) >= 8:
            # Check if it looks like a standup from title
            title_lower = meeting.title.lower()
            if any(k in title_lower for k in ("standup", "stand-up", "daily", "scrum", "huddle")):
                anomalies.append(
                    Anomaly(
                        entity_id=mid,
                        entity_type="meeting",
                        anomaly_type="oversized_standup",
                        severity="medium",
                        description=(
                            f'"{meeting.title}" has {len(meeting.attendee_emails)} attendees '
                            f"— far above the ideal range of 3-10 for a standup."
                        ),
                    )
                )

    return cascades, anomalies


# ============================================================================
# Network graph
# ============================================================================

def build_network(
    meetings: list[Meeting],
    focus_scores: list[FocusTimeScore],
    costs: dict[str, float],
) -> "NetworkGraph | None":
    """Co-occurrence graph. Nodes=people, edges=shared meetings."""
    if not meetings:
        return None

    focus_map: dict[str, FocusTimeScore] = {fs.person_email: fs for fs in focus_scores}

    # Gather all unique people
    all_people: set[str] = set()
    for meeting in meetings:
        for email in meeting.attendee_emails:
            all_people.add(str(email))

    if not all_people:
        return None

    total_people = len(all_people)

    # Build co-occurrence counts and combined costs between pairs
    co_occur: dict[tuple[str, str], int] = defaultdict(int)
    combined_cost: dict[tuple[str, str], float] = defaultdict(float)

    for meeting in meetings:
        people_list = sorted(set(str(e) for e in meeting.attendee_emails))
        cost = costs.get(str(meeting.meeting_id), 0.0)
        for a, b in combinations(people_list, 2):
            pair = (min(a, b), max(a, b))
            co_occur[pair] += 1
            combined_cost[pair] += cost

    # Build unique_connections per person
    unique_connections: dict[str, set[str]] = defaultdict(set)
    for (a, b) in co_occur:
        unique_connections[a].add(b)
        unique_connections[b].add(a)

    # Person hours
    person_hours: dict[str, float] = defaultdict(float)
    for meeting in meetings:
        dur_h = meeting.duration_minutes / 60.0
        for email in meeting.attendee_emails:
            person_hours[str(email)] += dur_h

    nodes: list[PersonNode] = []
    for person_email in all_people:
        centrality = (
            len(unique_connections[person_email]) / (total_people - 1)
            if total_people > 1
            else 0.0
        )
        fs = focus_map.get(person_email)
        focus_pct = fs.focus_percentage if fs else 1.0
        at_risk = focus_pct < 0.15

        nodes.append(
            PersonNode(
                email=person_email,
                display_name=person_email.split("@")[0].replace(".", " ").title(),
                total_meeting_hours=round(person_hours[person_email], 2),
                centrality_score=round(min(1.0, centrality), 4),
                focus_percentage=round(focus_pct, 4),
                at_risk=at_risk,
            )
        )

    edges: list[MeetingEdge] = [
        MeetingEdge(
            person_a=pair[0],
            person_b=pair[1],
            co_occurrence_count=count,
            combined_cost=round(combined_cost[pair], 2),
        )
        for pair, count in sorted(co_occur.items(), key=lambda x: combined_cost[x[0]], reverse=True)
    ]

    most_central = max(nodes, key=lambda n: n.centrality_score).email if nodes else ""
    highest_cost_pair = (edges[0].person_a, edges[0].person_b) if edges else ("", "")

    return NetworkGraph(
        nodes=nodes,
        edges=edges,
        most_central_person=most_central,
        highest_cost_pair=highest_cost_pair,
    )


# ============================================================================
# Recommendations
# ============================================================================

def compute_recommendations(
    waste_scores: list[WasteScore],
    meetings: list[Meeting],
    classifications: list[MeetingClassification],
    recurrence: dict[str, dict] | None = None,
) -> list[Recommendation]:
    """Decision-tree recommendations per meeting — with meeting-specific reasoning."""
    if recurrence is None:
        recurrence = {}

    meeting_map: dict[str, Meeting] = {str(m.meeting_id): m for m in meetings}
    class_map: dict[str, str] = {str(mc.meeting_id): mc.meeting_type for mc in classifications}

    # Human-readable action hints by meeting type
    _TYPE_TIPS: dict[str, str] = {
        "standup":      "Keep standups under 15 min with a strict round-robin format.",
        "1:1":          "Let the direct report drive the agenda with written updates beforehand.",
        "planning":     "Circulate a pre-read 24 h before so the session stays in decision mode.",
        "decision":     "Open with the decision statement; close only when an owner and date are assigned.",
        "brainstorm":   "Time-box ideation, then vote — avoid open-ended discussion with no output.",
        "status-update": "Replace verbal updates with a shared async doc; use the meeting only for blockers.",
        "social":       "Social meetings are intentionally low-structure — no action needed.",
    }

    results: list[Recommendation] = []

    for ws in waste_scores:
        mid = str(ws.meeting_id)
        meeting = meeting_map.get(mid)
        if not meeting:
            continue

        composite = ws.composite_score
        rec_data = recurrence.get(mid, {})
        staleness = rec_data.get("staleness_score", 0.0)
        is_recurring = meeting.is_recurring
        mtype = class_map.get(mid, "status-update")
        title = meeting.title
        n_attendees = len(meeting.attendee_emails)
        dur = meeting.duration_minutes
        tip = _TYPE_TIPS.get(mtype, "")

        # ── Decision tree ────────────────────────────────────────────────────
        if composite >= 0.65 and is_recurring and ws.decision_deficit > 0.6:
            action, priority = "cancel", 1
            reasoning = (
                f"'{title}' is a recurring {mtype} with a {composite:.0%} waste score and almost "
                f"no recorded decisions ({ws.decision_deficit:.0%} deficit). "
                f"No outcomes + recurring cost = meeting that has outlived its purpose. "
                f"Cancel and replace with an async update."
            )

        elif composite >= 0.55 and staleness > 0.5:
            action, priority = "cancel", 1
            reasoning = (
                f"'{title}' scores {composite:.0%} waste and its recurring series is showing "
                f"staleness ({staleness:.0%}). Declining engagement signals this series is no longer "
                f"delivering value. Cancel or restructure into a quarterly check-in instead."
            )

        elif composite >= 0.50 and ws.participation_imbalance > 0.4:
            action, priority = "restructure", 2
            reasoning = (
                f"'{title}' has high participation imbalance ({ws.participation_imbalance:.0%}) — "
                f"most of the {n_attendees} attendees are passive observers. "
                f"Split into a small decision group (3–5 people) and send the rest an async summary. "
                + tip
            )

        elif composite >= 0.45 and ws.cost_factor > 0.5:
            action, priority = "shorten", 3
            reasoning = (
                f"'{title}' is one of the costlier meetings ({n_attendees} people × {dur} min) "
                f"with a {composite:.0%} waste score. "
                f"Cut duration by 30% and enforce a written agenda at least 2 hours before. "
                + tip
            )

        elif composite >= 0.30:
            action, priority = "shorten", 4
            # Build a specific reason based on which component is highest
            worst_dim, worst_val = max(
                [
                    ("cost", ws.cost_factor),
                    ("decision-making", ws.decision_deficit),
                    ("participation", ws.participation_imbalance),
                    ("recurrence", ws.recurrence_staleness),
                ],
                key=lambda x: x[1],
            )
            dim_advice = {
                "cost":          f"It costs more than similar {mtype} meetings — trim duration.",
                "decision-making": "No decisions were recorded. End every session with explicit owners and due dates.",
                "participation": "Several attendees may not need to be present — move them to async.",
                "recurrence":    "The recurring format feels stale. Add a 'should this meeting still exist?' agenda item.",
            }
            reasoning = (
                f"'{title}' ({mtype}, {dur} min, {n_attendees} people) scores {composite:.0%} waste. "
                f"Biggest driver: {worst_dim} ({worst_val:.0%}). "
                + dim_advice.get(worst_dim, "") + " " + tip
            ).strip()

        else:
            action, priority = "keep", 5
            reasoning = (
                f"'{title}' scores {composite:.0%} waste — within acceptable range for a {mtype}. "
                f"{'Recurring pattern looks healthy.' if is_recurring else 'No changes needed.'} "
                + tip
            ).strip()

        results.append(
            Recommendation(
                meeting_id=meeting.meeting_id,
                recommended_action=action,  # type: ignore[arg-type]
                reasoning=reasoning,
                priority=priority,
            )
        )

    # Sort by priority
    results.sort(key=lambda r: r.priority)
    return results


# ============================================================================
# Interventions
# ============================================================================

def compute_interventions(
    waste_scores: list[WasteScore],
    meetings: list[Meeting],
    classifications: list[MeetingClassification],
) -> list[Intervention]:
    """Template-based email + agenda for high-waste recurring meetings."""
    meeting_map: dict[str, Meeting] = {str(m.meeting_id): m for m in meetings}
    class_map: dict[str, str] = {str(mc.meeting_id): mc.meeting_type for mc in classifications}

    results: list[Intervention] = []

    for ws in waste_scores:
        # Only intervene on medium-high waste recurring meetings
        if ws.composite_score < 0.40:
            continue
        mid = str(ws.meeting_id)
        meeting = meeting_map.get(mid)
        if not meeting or not meeting.is_recurring:
            continue

        meeting_type = class_map.get(mid, "status-update")
        attendees = list(str(e) for e in meeting.attendee_emails)
        organizer = str(meeting.organizer_email) if meeting.organizer_email else ""

        email_template = (
            f"Subject: Making '{meeting.title}' more effective\n\n"
            f"Hi team,\n\n"
            f"I'd like to revisit how we run '{meeting.title}' to ensure everyone's time "
            f"is used effectively. Our analysis suggests this meeting may benefit from "
            f"a tighter format.\n\n"
            f"Going forward:\n"
            f"- We'll keep strictly to the agenda below.\n"
            f"- Decisions and action items will be captured in real time.\n"
            f"- Anyone who doesn't have a direct role is welcome to receive a summary instead.\n\n"
            f"Please review the agenda before the meeting.\n\nThanks,\n{organizer or 'The Organizer'}"
        )

        if meeting_type == "standup":
            agenda = [
                "Round-robin: what did you finish yesterday? (30s each)",
                "Round-robin: what are you doing today? (30s each)",
                "Blockers only — raise if you're blocked",
                "No problem-solving in standup — take offline",
            ]
            format_tip = "Consider async standup bot (Geekbot/Standuply) if attendance is low."
        elif meeting_type == "1:1":
            agenda = [
                "Updates (5 min)",
                "Priorities and blockers (10 min)",
                "Feedback and development (5 min)",
                "Action items review",
            ]
            format_tip = "1:1s are most effective when the direct report leads the agenda."
        elif meeting_type == "planning":
            agenda = [
                "Review goals and OKRs (10 min)",
                "Backlog prioritisation (20 min)",
                "Capacity planning (10 min)",
                "Decisions and action items (10 min)",
                "Open Q&A (10 min)",
            ]
            format_tip = "Distribute pre-read materials 24 hours before to avoid reading in the room."
        else:
            agenda = [
                "State the goal of this meeting (2 min)",
                "Updates — written, not verbal (5 min)",
                "Discussion items requiring group input (15 min)",
                "Decisions and owner assignments (5 min)",
                "Next steps and next meeting purpose",
            ]
            format_tip = "Consider converting status updates to async channels (email / Slack)."

        # Recommend attendee reduction for over-attended meetings
        norm = _TYPE_NORMS.get(meeting_type, 8)
        excess = max(0, len(attendees) - norm)
        reduction_list = attendees[-excess:] if excess > 0 else []

        results.append(
            Intervention(
                meeting_id=meeting.meeting_id,
                pre_meeting_email_template=email_template,
                suggested_agenda=agenda,
                recommended_attendee_reduction=reduction_list,
                alternative_format=format_tip,
            )
        )

    return results


# ============================================================================
# ROI projection
# ============================================================================

_WEEKS_PER_YEAR = 52


def compute_roi(
    waste_scores: list[WasteScore],
    recommendations: list[Recommendation],
    costs: dict[str, float],
    meeting_titles: dict[str, str] | None = None,
) -> ROIProjection:
    """Sum savings from cancel (annual cost) and shorten (50% of annual cost) recs."""
    rec_map: dict[str, Recommendation] = {str(r.meeting_id): r for r in recommendations}

    cancel_savings = 0.0
    shorten_savings = 0.0
    top_changes: list[str] = []

    for ws in waste_scores:
        mid = str(ws.meeting_id)
        rec = rec_map.get(mid)
        if not rec:
            continue

        meeting_cost = costs.get(mid, 0.0)
        # Estimate annual cost assuming weekly recurrence
        annual_cost = meeting_cost * _WEEKS_PER_YEAR

        title = (meeting_titles or {}).get(mid)
        label = f"'{title[:28]}'" if title else f"(id: {mid[:8]}…)"

        if rec.recommended_action == "cancel":
            cancel_savings += annual_cost
            top_changes.append(f"Cancel {label}: saves ${annual_cost:,.0f}/yr")
        elif rec.recommended_action == "shorten":
            shorten_savings += annual_cost * 0.5
            top_changes.append(f"Shorten {label}: saves ${annual_cost * 0.5:,.0f}/yr")

    total_saving = round(cancel_savings + shorten_savings, 2)
    # Break-even in weeks: assume 4 hours effort to implement each change
    num_changes = sum(1 for r in recommendations if r.recommended_action in ("cancel", "shorten"))
    implementation_cost = num_changes * 4 * 75  # 4h * $75/hr

    if total_saving > 0:
        weeks_to_break_even = max(1, round((implementation_cost / (total_saving / _WEEKS_PER_YEAR))))
    else:
        weeks_to_break_even = 0

    # Deduplicate by label — keep the highest-saving entry per unique label
    seen: dict[str, str] = {}
    for change in top_changes:
        # Key = everything before the colon (e.g. "Shorten 'Weekly Status Update'")
        key = change.split(":")[0]
        if key not in seen:
            seen[key] = change
    # Sort deduplicated list by saving value descending
    deduped = sorted(seen.values(), key=lambda s: float(s.split("$")[1].replace(",", "").split("/")[0]) if "$" in s else 0, reverse=True)
    top_changes = deduped[:5]

    return ROIProjection(
        projected_annual_saving=total_saving,
        weeks_to_break_even=weeks_to_break_even,
        top_changes=top_changes,
        assumptions=[
            "Assumes weekly recurrence for all recurring meetings",
            "Cancellation saves 100% of per-meeting cost × 52 weeks",
            "Shortening saves 50% of per-meeting cost × 52 weeks",
            f"Hourly rate assumed at ${75:.0f}/hr",
            "Does not account for one-off meetings",
        ],
    )

# Made with Bob