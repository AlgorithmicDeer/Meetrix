"""
LLM-backed nodes — exactly 2 LLM calls in the entire pipeline.
1. extract_insights_node  — extract action items + decisions from all meetings.
2. synthesize_report_node — generate executive report from compact summary.
"""
import asyncio
import json
import logging
from typing import Any

from app.config import settings
from app.llm import get_llm
from app.models.schemas import ActionItem, ExecutiveReport

logger = logging.getLogger(__name__)


# ============================================================================
# Node 1: Extract action items and decisions (ONE LLM call)
# ============================================================================

async def extract_insights_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Single LLM call: process all meetings with notes/transcripts together.
    Returns action_items list and decisions dict (meeting_id -> list[str]).
    On any failure: return empty results rather than crashing the pipeline.
    """
    meetings = state.get("validated_meetings", [])
    transcripts: dict[str, str] = state.get("transcripts", {})

    # Filter to meetings that have notes or a transcript
    meetings_with_content = [
        m for m in meetings
        if (m.notes_text and m.notes_text.strip())
        or transcripts.get(str(m.meeting_id), "").strip()
    ]

    if not meetings_with_content:
        logger.info("extract_insights_node: no meetings with content — skipping LLM call")
        return {"action_items": [], "decisions": {}}

    # Build the prompt for all meetings in one batch
    meeting_blocks: list[str] = []
    for m in meetings_with_content:
        mid = str(m.meeting_id)
        notes = (m.notes_text or "").strip()
        transcript = transcripts.get(mid, "").strip()
        block = (
            f"Meeting ID: {mid}\n"
            f"Title: {m.title}\n"
            f"Attendees: {', '.join(str(e) for e in m.attendee_emails)}"
        )
        if notes:
            block += f"\nNotes: {notes}"
        if transcript:
            block += f"\nTranscript: {transcript[:3000]}"  # cap per meeting to fit context
        meeting_blocks.append(block)

    meetings_text = "\n---\n".join(meeting_blocks)

    system_prompt = (
        "You are an assistant that extracts structured information from meeting notes and transcripts. "
        "For each meeting provided, extract:\n"
        "1. Action items: specific tasks assigned to someone, with the assignee email if mentioned.\n"
        "2. Decisions: explicit decisions that were made (e.g., 'We decided to...', 'Approved: ...').\n\n"
        "Return a JSON array. Each element must have:\n"
        "  meeting_id: string (exact Meeting ID from input)\n"
        "  action_items: array of {description: string, assignee_email: string or null}\n"
        "  decisions: array of strings\n\n"
        "If no action items or decisions were found for a meeting, use empty arrays. "
        "Return ONLY valid JSON — no markdown, no explanation."
    )

    user_prompt = (
        f"Extract action items and decisions from the following {len(meetings_with_content)} meetings:\n\n"
        f"{meetings_text}"
    )

    try:
        llm = get_llm(model_name=settings.ACTION_ITEM_MODEL, temperature=0.0)

        async with asyncio.timeout(settings.LLM_TIMEOUT_SECONDS):
            response = await llm.ainvoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )

        raw_text = response.content if hasattr(response, "content") else str(response)

        # Strip markdown code fences if present
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed = json.loads(raw_text)

        action_items: list[ActionItem] = []
        decisions: dict[str, list[str]] = {}

        # Build valid meeting_id set for validation
        valid_ids = {str(m.meeting_id) for m in meetings}

        for entry in parsed:
            entry_mid = str(entry.get("meeting_id", ""))
            if entry_mid not in valid_ids:
                continue

            # Find the original Meeting object for the UUID
            meeting_obj = next((m for m in meetings if str(m.meeting_id) == entry_mid), None)
            if not meeting_obj:
                continue

            for ai in entry.get("action_items", []):
                desc = ai.get("description", "").strip()
                if not desc:
                    continue
                assignee = ai.get("assignee_email") or None
                action_items.append(
                    ActionItem(
                        meeting_id=meeting_obj.meeting_id,
                        description=desc,
                        assignee_email=assignee,
                        followed_through=None,
                    )
                )

            entry_decisions = [d.strip() for d in entry.get("decisions", []) if d.strip()]
            if entry_decisions:
                decisions[entry_mid] = entry_decisions

        logger.info(
            f"extract_insights_node: extracted {len(action_items)} action items, "
            f"{sum(len(v) for v in decisions.values())} decisions across "
            f"{len(meetings_with_content)} meetings"
        )
        return {"action_items": action_items, "decisions": decisions}

    except asyncio.TimeoutError:
        logger.warning(
            f"extract_insights_node timed out after {settings.LLM_TIMEOUT_SECONDS}s — returning empty"
        )
        return {"action_items": [], "decisions": {}}
    except json.JSONDecodeError as e:
        logger.warning(f"extract_insights_node: JSON parse error: {e} — returning empty")
        return {"action_items": [], "decisions": {}}
    except Exception as e:
        logger.error(f"extract_insights_node failed: {e}")
        return {"action_items": [], "decisions": {}}


# ============================================================================
# Node 2: Synthesize executive report (ONE LLM call)
# ============================================================================

async def synthesize_report_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Single LLM call: generate executive report from compact summary of all analysis.
    On any failure: build a fallback report algorithmically rather than crashing.
    """
    meetings = state.get("validated_meetings", [])
    waste_scores = state.get("waste_scores", [])
    focus_scores = state.get("focus_scores", [])
    meeting_health_scores = state.get("meeting_health_scores", [])
    cascade_chains = state.get("cascade_chains", [])
    recommendations = state.get("recommendations", [])
    costs: dict[str, float] = state.get("costs", {})

    total_meetings = len(meetings)
    total_cost = round(sum(costs.values()), 2)

    # Compute meetrix_score algorithmically
    avg_waste = (
        sum(ws.composite_score for ws in waste_scores) / len(waste_scores)
        if waste_scores else 0.0
    )
    avg_health = (
        sum(mh.overall_health_score for mh in meeting_health_scores) / len(meeting_health_scores)
        if meeting_health_scores else 0.5
    )
    avg_focus = (
        sum(fs.focus_percentage for fs in focus_scores) / len(focus_scores)
        if focus_scores else 0.5
    )

    focus_penalty = max(0.0, 0.5 - avg_focus) * 2  # 0-1 scale
    health_penalty = max(0.0, 0.5 - avg_health) * 2

    meetrix_score = max(
        0,
        round(100 - avg_waste * 60 - focus_penalty * 25 - health_penalty * 15),
    )

    # Date range
    if meetings:
        dates = [m.start_datetime for m in meetings]
        period = f"{min(dates).strftime('%b %d')} – {max(dates).strftime('%b %d, %Y')}"
    else:
        period = "Unknown period"

    # Top 5 high-waste meetings summary
    top_waste = sorted(waste_scores, key=lambda ws: ws.composite_score, reverse=True)[:5]
    meeting_map = {str(m.meeting_id): m for m in meetings}

    top_waste_text = ""
    for ws in top_waste:
        m = meeting_map.get(str(ws.meeting_id))
        title = m.title if m else str(ws.meeting_id)[:8]
        top_waste_text += f"  - {title}: {ws.composite_score:.2f} ({ws.category})\n"

    people_overloaded = sum(1 for fs in focus_scores if fs.focus_percentage < 0.15)
    cascade_total_cost = sum(c.total_cascade_cost for c in cascade_chains)

    top_recs_text = "\n".join(
        f"  {i+1}. {r.recommended_action.upper()} — {r.reasoning[:120]}"
        for i, r in enumerate(recommendations[:3])
    )

    system_prompt = (
        "You are a management consultant writing a concise executive briefing for leadership. "
        "Focus on impact, cost, and actionable recommendations. Be specific with numbers. "
        "Write in a direct, professional tone. Do not add preamble or meta-commentary.\n\n"
        "Return valid JSON with exactly these keys:\n"
        "  summary: string (3 paragraphs, ~200 words total)\n"
        "  key_findings: array of exactly 5 strings\n"
        "  top_recommendations: array of exactly 5 strings\n"
        "Return ONLY the JSON object. No markdown fences."
    )

    user_prompt = (
        f"Write an executive briefing based on the following meeting analysis:\n\n"
        f"Period: {period}\n"
        f"Total meetings analysed: {total_meetings}\n"
        f"Total meeting cost: ${total_cost:,.0f}\n"
        f"Meetrix score: {meetrix_score}/100\n"
        f"Average waste score: {avg_waste:.2f}/1.00\n"
        f"People in critical focus overload: {people_overloaded}\n"
        f"Cascade chains detected: {len(cascade_chains)} (total wasted cost: ${cascade_total_cost:,.0f})\n\n"
        f"Top 5 highest-waste meetings:\n{top_waste_text}\n"
        f"Top 3 recommendations:\n{top_recs_text}\n"
    )

    try:
        llm = get_llm(model_name=settings.REPORT_GENERATION_MODEL, temperature=0.3)

        async with asyncio.timeout(settings.REPORT_TIMEOUT_SECONDS):
            response = await llm.ainvoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )

        raw_text = response.content if hasattr(response, "content") else str(response)
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        parsed = json.loads(raw_text)

        summary_text = str(parsed.get("summary", ""))
        key_findings = [str(f) for f in parsed.get("key_findings", [])][:5]
        top_recs = [str(r) for r in parsed.get("top_recommendations", [])][:5]

        # Pad to 5 items if LLM returned fewer
        while len(key_findings) < 5:
            key_findings.append("No additional findings identified.")
        while len(top_recs) < 5:
            top_recs.append("No additional recommendations.")

    except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
        logger.warning(
            f"synthesize_report_node LLM call failed ({type(e).__name__}: {e}) — using fallback"
        )
        summary_text = _build_fallback_summary(
            total_meetings, total_cost, meetrix_score, avg_waste, people_overloaded, cascade_chains
        )
        key_findings = _build_fallback_findings(
            waste_scores, focus_scores, cascade_chains, costs, meeting_map
        )
        top_recs = [r.reasoning[:200] for r in recommendations[:5]]
        while len(top_recs) < 5:
            top_recs.append("Review remaining meetings for efficiency improvements.")

    executive_report = ExecutiveReport(
        period=period,
        total_cost=total_cost,
        total_meetings=total_meetings,
        meetrix_score=meetrix_score,
        summary=summary_text,
        key_findings=key_findings,
        top_recommendations=top_recs,
        trend_direction="stable",
        data_residency="All data processed and stored locally. No external API calls.",
    )

    logger.info(
        f"synthesize_report_node: report generated — meetrix_score={meetrix_score}, "
        f"total_cost=${total_cost:,.0f}"
    )
    return {"executive_report": executive_report}


# ============================================================================
# Fallback helpers (used when LLM is unavailable)
# ============================================================================

def _build_fallback_summary(
    total_meetings: int,
    total_cost: float,
    meetrix_score: int,
    avg_waste: float,
    people_overloaded: int,
    cascade_chains: list,
) -> str:
    return (
        f"Analysis of {total_meetings} meetings reveals a total meeting cost of ${total_cost:,.0f} "
        f"with an average waste score of {avg_waste:.2f}/1.00. The overall Meetrix score is "
        f"{meetrix_score}/100, indicating {'significant' if meetrix_score < 50 else 'moderate'} "
        f"room for improvement in meeting culture.\n\n"
        f"{people_overloaded} {'person is' if people_overloaded == 1 else 'people are'} in critical "
        f"focus overload, spending over 85% of working hours in meetings. "
        f"{len(cascade_chains)} cascade chains were detected, where one poorly-run meeting "
        f"spawned multiple follow-up meetings.\n\n"
        f"Immediate actions should focus on cancelling or shortening the highest-waste recurring "
        f"meetings and introducing async alternatives where appropriate."
    )


def _build_fallback_findings(
    waste_scores: list,
    focus_scores: list,
    cascade_chains: list,
    costs: dict,
    meeting_map: dict,
) -> list[str]:
    findings: list[str] = []

    high_waste = [ws for ws in waste_scores if ws.category == "High Waste"]
    if high_waste:
        findings.append(
            f"{len(high_waste)} meetings classified as High Waste, representing the largest "
            f"opportunity for cost reduction."
        )

    overloaded = [fs for fs in focus_scores if fs.focus_percentage < 0.15]
    if overloaded:
        findings.append(
            f"{len(overloaded)} team members have less than 15% focus time, indicating severe "
            f"meeting overload that reduces deep work capacity."
        )

    if cascade_chains:
        total_cascade_cost = sum(c.total_cascade_cost for c in cascade_chains)
        findings.append(
            f"{len(cascade_chains)} cascade chains detected — meetings spawning further meetings "
            f"— costing an estimated ${total_cascade_cost:,.0f} in compounded waste."
        )

    recurring_waste = [
        ws for ws in waste_scores
        if ws.composite_score >= 0.65
        and meeting_map.get(str(ws.meeting_id)) is not None
        and getattr(meeting_map.get(str(ws.meeting_id)), "is_recurring", False)
    ]
    if recurring_waste:
        findings.append(
            f"{len(recurring_waste)} high-waste meetings are recurring — eliminating these would "
            f"compound savings over time."
        )

    avg_decision_deficit = (
        sum(ws.decision_deficit for ws in waste_scores) / len(waste_scores)
        if waste_scores else 0
    )
    if avg_decision_deficit > 0.6:
        findings.append(
            f"Average decision deficit of {avg_decision_deficit:.2f} suggests most meetings lack "
            f"clear outcomes — structured agendas and pre-reads are recommended."
        )

    while len(findings) < 5:
        findings.append("Review meeting cadence and purpose with all team leads.")

    return findings[:5]

# Made with Bob
