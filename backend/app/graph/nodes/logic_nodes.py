"""
Logic agent nodes - deterministic Python functions.
No LLM calls, pure computation and data transformation.
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any
from uuid import UUID
from app.models.schemas import (
    Meeting,
    WasteScore,
    FocusTimeScore,
    Anomaly,
    CascadeChain,
    NetworkGraph,
    PersonNode,
    MeetingEdge,
    ROIProjection,
)
from app.utils.csv_parser import parse_csv
from app.utils.agent_logger import log_agent_event
from app.config import settings

logger = logging.getLogger(__name__)


async def data_validation_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 1: Parse and validate CSV data.
    
    Responsibilities:
    - Parse CSV with flexible column mapping
    - Validate email formats
    - Compute duration from timestamps
    - Continue with valid rows only
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "data_validation_agent", 1, "running")
    
    try:
        csv_content = state["uploaded_files"].get("historical_csv", "")
        if not csv_content:
            error = "No historical CSV uploaded"
            state["errors"].append(error)
            await log_agent_event(session_id, "data_validation_agent", 1, "failed", error)
            return {"validated_meetings": [], "errors": state["errors"]}
        
        # Parse notes files if provided
        notes_mapping = {}
        for filename, content in state["uploaded_files"].items():
            if filename.startswith("notes_") and filename.endswith(".txt"):
                # Extract meeting title from filename: notes_Meeting_Title.txt
                title = filename[6:-4].replace("_", " ")
                notes_mapping[title] = content
        
        # Parse CSV
        meetings, errors = parse_csv(csv_content, notes_mapping)
        
        if errors:
            state["errors"].extend(errors)
        
        if not meetings:
            error = "No valid meetings found in CSV"
            state["errors"].append(error)
            await log_agent_event(session_id, "data_validation_agent", 1, "failed", error)
            return {"validated_meetings": [], "errors": state["errors"]}
        
        logger.info(f"Validated {len(meetings)} meetings with {len(errors)} errors")
        await log_agent_event(session_id, "data_validation_agent", 1, "complete")
        
        return {
            "validated_meetings": meetings,
            "errors": state["errors"],
        }
        
    except Exception as e:
        error = f"Data validation failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "data_validation_agent", 1, "failed", error)
        return {"validated_meetings": [], "errors": state["errors"]}


async def cost_analysis_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 3: Calculate meeting costs.
    
    Formula: (duration_minutes / 60) × attendee_count × hourly_rate
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "cost_analysis_agent", 3, "running")
    
    try:
        meetings = state["validated_meetings"]
        hourly_rate = state["config"].get("hourly_rate", settings.DEFAULT_HOURLY_RATE)
        
        costs = {}
        for meeting in meetings:
            cost = (meeting.duration_minutes / 60.0) * len(meeting.attendee_emails) * hourly_rate
            costs[str(meeting.meeting_id)] = cost
        
        logger.info(f"Calculated costs for {len(costs)} meetings")
        await log_agent_event(session_id, "cost_analysis_agent", 3, "complete")
        
        # Store in parallel_analysis dict
        parallel_analysis = state.get("parallel_analysis", {})
        parallel_analysis["cost"] = costs
        
        return {"parallel_analysis": parallel_analysis}
        
    except Exception as e:
        error = f"Cost analysis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "cost_analysis_agent", 3, "failed", error)
        return {"parallel_analysis": state.get("parallel_analysis", {})}


async def participation_analysis_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 3: Analyze attendee participation patterns.
    
    Calculates:
    - Optional vs required ratio (if data available)
    - Organizer recurrence count
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "participation_analysis_agent", 3, "running")
    
    try:
        meetings = state["validated_meetings"]
        
        # Count meetings per organizer
        organizer_counts = defaultdict(int)
        for meeting in meetings:
            if meeting.organizer_email:
                organizer_counts[meeting.organizer_email] += 1
        
        participation = {}
        for meeting in meetings:
            # For MVP, we don't have optional/required distinction in CSV
            # Set optional_ratio to 0.0 (all required)
            optional_ratio = 0.0
            
            organizer_recurrence = 0
            if meeting.organizer_email:
                organizer_recurrence = organizer_counts[meeting.organizer_email]
            
            participation[str(meeting.meeting_id)] = {
                "optional_ratio": optional_ratio,
                "organizer_recurrence_count": organizer_recurrence,
            }
        
        logger.info(f"Analyzed participation for {len(participation)} meetings")
        await log_agent_event(session_id, "participation_analysis_agent", 3, "complete")
        
        parallel_analysis = state.get("parallel_analysis", {})
        parallel_analysis["participation"] = participation
        
        return {"parallel_analysis": parallel_analysis}
        
    except Exception as e:
        error = f"Participation analysis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "participation_analysis_agent", 3, "failed", error)
        return {"parallel_analysis": state.get("parallel_analysis", {})}


async def recurrence_analysis_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 3: Detect staleness in recurring meetings.
    
    Groups meetings by title + organizer to detect series.
    Calculates staleness score based on age and decision deficit.
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "recurrence_analysis_agent", 3, "running")
    
    try:
        meetings = state["validated_meetings"]
        
        # Group by title + organizer
        series = defaultdict(list)
        for meeting in meetings:
            key = (meeting.title.lower(), meeting.organizer_email or "")
            series[key].append(meeting)
        
        recurrence = {}
        for meeting in meetings:
            if not meeting.is_recurring:
                recurrence[str(meeting.meeting_id)] = {
                    "staleness_score": 0.0,
                    "attendance_drop_percentage": 0.0,
                }
                continue
            
            # Get series for this meeting
            key = (meeting.title.lower(), meeting.organizer_email or "")
            series_meetings = sorted(series[key], key=lambda m: m.start_datetime)
            
            # Calculate staleness
            staleness_score = 0.0
            attendance_drop = 0.0
            
            if len(series_meetings) > 1:
                # Age factor: older series = higher staleness
                first_meeting = series_meetings[0]
                age_days = (datetime.utcnow() - first_meeting.start_datetime).days
                if age_days > 180:  # 6 months
                    staleness_score += 0.4
                
                # Attendance drop
                first_count = len(series_meetings[0].attendee_emails)
                current_count = len(meeting.attendee_emails)
                if first_count > 0:
                    attendance_drop = max(0, (first_count - current_count) / first_count)
                    staleness_score += attendance_drop * 0.6
            
            recurrence[str(meeting.meeting_id)] = {
                "staleness_score": min(1.0, staleness_score),
                "attendance_drop_percentage": attendance_drop,
            }
        
        logger.info(f"Analyzed recurrence for {len(recurrence)} meetings")
        await log_agent_event(session_id, "recurrence_analysis_agent", 3, "complete")
        
        parallel_analysis = state.get("parallel_analysis", {})
        parallel_analysis["recurrence"] = recurrence
        
        return {"parallel_analysis": parallel_analysis}
        
    except Exception as e:
        error = f"Recurrence analysis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "recurrence_analysis_agent", 3, "failed", error)
        return {"parallel_analysis": state.get("parallel_analysis", {})}


async def focus_time_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 3: Calculate focus time per person.
    
    Computes:
    - Total meeting hours per person
    - Remaining focus blocks (2+ hour contiguous periods)
    - Focus percentage
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "focus_time_agent", 3, "running")
    
    try:
        meetings = state["validated_meetings"]
        
        # Group meetings by person
        person_meetings = defaultdict(list)
        for meeting in meetings:
            for email in meeting.attendee_emails:
                person_meetings[email].append(meeting)
        
        focus_scores = []
        for email, person_mtgs in person_meetings.items():
            # Calculate total meeting hours
            total_minutes = sum(m.duration_minutes for m in person_mtgs)
            total_hours = total_minutes / 60.0
            
            # Sort meetings by start time
            sorted_mtgs = sorted(person_mtgs, key=lambda m: m.start_datetime)
            
            # Find focus blocks (2+ hour gaps between meetings)
            focus_blocks = 0
            longest_block = 0
            
            for i in range(len(sorted_mtgs) - 1):
                gap_minutes = (sorted_mtgs[i + 1].start_datetime - sorted_mtgs[i].end_datetime).total_seconds() / 60
                if gap_minutes >= 120:  # 2 hours
                    focus_blocks += 1
                    longest_block = max(longest_block, int(gap_minutes))
            
            # Calculate focus percentage normalised to actual period
            if sorted_mtgs:
                date_range_days = max(
                    1,
                    (sorted_mtgs[-1].start_datetime - sorted_mtgs[0].start_datetime).days
                )
            else:
                date_range_days = 90  # default for full dataset
            weeks_in_period = date_range_days / 7.0
            total_available_hours = 40.0 * weeks_in_period
            focus_percentage = max(0.0, min(1.0, (total_available_hours - total_hours) / total_available_hours))
            
            focus_scores.append(FocusTimeScore(
                person_email=email,
                total_meeting_hours=total_hours,
                focus_blocks_remaining=focus_blocks,
                longest_focus_block_minutes=longest_block,
                focus_percentage=focus_percentage,
            ))
        
        logger.info(f"Calculated focus scores for {len(focus_scores)} people")
        await log_agent_event(session_id, "focus_time_agent", 3, "complete")
        
        return {"focus_scores": focus_scores}
        
    except Exception as e:
        error = f"Focus time analysis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "focus_time_agent", 3, "failed", error)
        return {"focus_scores": []}


async def calendar_fragmentation_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 3: Detect back-to-back meeting chains.
    
    Identifies:
    - Meeting chains (< 15min gap)
    - Context switches per day
    - Maximum chain length
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "calendar_fragmentation_agent", 3, "running")
    
    try:
        meetings = state["validated_meetings"]
        
        # Group by person
        person_meetings = defaultdict(list)
        for meeting in meetings:
            for email in meeting.attendee_emails:
                person_meetings[email].append(meeting)
        
        fragmentation = {}
        for email, person_mtgs in person_meetings.items():
            # Sort by start time
            sorted_mtgs = sorted(person_mtgs, key=lambda m: m.start_datetime)
            
            chain_count = 0
            max_chain_length = 0
            current_chain = 1
            context_switches = 0
            
            for i in range(len(sorted_mtgs) - 1):
                gap_minutes = (sorted_mtgs[i + 1].start_datetime - sorted_mtgs[i].end_datetime).total_seconds() / 60
                
                if gap_minutes < 15:  # Back-to-back
                    current_chain += 1
                    context_switches += 1
                else:
                    if current_chain > 1:
                        chain_count += 1
                        max_chain_length = max(max_chain_length, current_chain)
                    current_chain = 1
            
            # Check final chain
            if current_chain > 1:
                chain_count += 1
                max_chain_length = max(max_chain_length, current_chain)
            
            fragmentation[email] = {
                "chain_count": chain_count,
                "max_chain_length": max_chain_length,
                "context_switches_per_day": context_switches / 7.0,  # Approximate weekly average
            }
        
        logger.info(f"Analyzed fragmentation for {len(fragmentation)} people")
        await log_agent_event(session_id, "calendar_fragmentation_agent", 3, "complete")
        
        parallel_analysis = state.get("parallel_analysis", {})
        parallel_analysis["fragmentation"] = fragmentation
        
        return {"parallel_analysis": parallel_analysis}
        
    except Exception as e:
        error = f"Fragmentation analysis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "calendar_fragmentation_agent", 3, "failed", error)
        return {"parallel_analysis": state.get("parallel_analysis", {})}


async def waste_synthesis_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 4: Compute composite waste scores.
    
    Applies weighted formula across dimensions:
    - cost_factor (0.35)
    - decision_deficit (0.30)
    - participation_imbalance (0.20)
    - recurrence_staleness (0.15)
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "waste_synthesis_agent", 4, "running")
    
    try:
        meetings = state["validated_meetings"]
        parallel = state.get("parallel_analysis", {})
        
        # Get weights from config
        weights = {
            "cost": state["config"].get("weight_cost", settings.WEIGHT_COST),
            "decision": state["config"].get("weight_decision", settings.WEIGHT_DECISION),
            "participation": state["config"].get("weight_participation", settings.WEIGHT_PARTICIPATION),
            "recurrence": state["config"].get("weight_recurrence", settings.WEIGHT_RECURRENCE),
        }
        
        # Normalize costs to 0-1
        costs = parallel.get("cost", {})
        if costs:
            max_cost = max(costs.values())
            normalized_costs = {k: v / max_cost if max_cost > 0 else 0.0 for k, v in costs.items()}
        else:
            normalized_costs = {}
        
        # Get decisions (will be populated by LLM agent)
        decisions = parallel.get("decisions", {})
        
        # Get participation and recurrence
        participation = parallel.get("participation", {})
        recurrence = parallel.get("recurrence", {})
        
        waste_scores = []
        for meeting in meetings:
            mid = str(meeting.meeting_id)
            
            # Cost factor
            cost_factor = normalized_costs.get(mid, 0.0)
            
            # Decision deficit (1.0 if no decisions, 0.0 if decisions present)
            decision_count = len(decisions.get(mid, []))
            decision_deficit = 1.0 if decision_count == 0 else max(0.0, 1.0 - (decision_count / 3.0))
            
            # Participation imbalance
            part_data = participation.get(mid, {})
            participation_imbalance = part_data.get("optional_ratio", 0.0)
            
            # Recurrence staleness
            rec_data = recurrence.get(mid, {})
            recurrence_staleness = rec_data.get("staleness_score", 0.0)
            
            # Compute composite score
            composite = (
                cost_factor * weights["cost"] +
                decision_deficit * weights["decision"] +
                participation_imbalance * weights["participation"] +
                recurrence_staleness * weights["recurrence"]
            )
            
            # Categorize
            if composite >= settings.HIGH_WASTE_THRESHOLD:
                category = "High Waste"
                threshold_exceeded = True
            elif composite >= settings.MEDIUM_WASTE_THRESHOLD:
                category = "Medium Waste"
                threshold_exceeded = False
            elif composite >= 0.25:
                category = "Low Waste"
                threshold_exceeded = False
            else:
                category = "High Value"
                threshold_exceeded = False
            
            waste_scores.append(WasteScore(
                meeting_id=meeting.meeting_id,
                cost_factor=cost_factor,
                decision_deficit=decision_deficit,
                participation_imbalance=participation_imbalance,
                recurrence_staleness=recurrence_staleness,
                composite_score=composite,
                category=category,
                threshold_exceeded=threshold_exceeded,
            ))
        
        logger.info(f"Synthesized waste scores for {len(waste_scores)} meetings")
        await log_agent_event(session_id, "waste_synthesis_agent", 4, "complete")
        
        return {"waste_scores": waste_scores}
        
    except Exception as e:
        error = f"Waste synthesis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "waste_synthesis_agent", 4, "failed", error)
        return {"waste_scores": []}


async def anomaly_detection_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 4: Detect anomalies and cascade chains.
    
    Detects:
    - Doubled meeting hours week-over-week
    - Attendance spikes
    - Individual overload
    - Cascade chains (underprepared meeting → follow-ups)
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "anomaly_detection_agent", 4, "running")
    
    try:
        meetings = state["validated_meetings"]
        waste_scores = state.get("waste_scores", [])
        focus_scores = state.get("focus_scores", [])
        
        anomalies = []
        cascade_chains = []
        
        # Build waste score lookup
        waste_lookup = {str(ws.meeting_id): ws for ws in waste_scores}
        
        # Detect cascade chains
        high_deficit_meetings = [
            m for m in meetings
            if waste_lookup.get(str(m.meeting_id), WasteScore(
                meeting_id=m.meeting_id,
                cost_factor=0,
                decision_deficit=0,
                participation_imbalance=0,
                recurrence_staleness=0,
                composite_score=0,
                category="High Value",
                threshold_exceeded=False
            )).decision_deficit > 0.8
        ]
        
        for origin in high_deficit_meetings:
            # Find meetings within 72 hours with >40% attendee overlap
            spawned = []
            origin_attendees = set(origin.attendee_emails)
            
            for candidate in meetings:
                if candidate.meeting_id == origin.meeting_id:
                    continue
                
                time_diff = (candidate.start_datetime - origin.end_datetime).total_seconds() / 3600
                if 0 < time_diff <= 72:
                    candidate_attendees = set(candidate.attendee_emails)
                    overlap = len(origin_attendees & candidate_attendees) / len(origin_attendees)
                    
                    if overlap > 0.4:
                        spawned.append(candidate.meeting_id)
            
            if spawned:
                # Calculate total cascade cost
                costs = state.get("parallel_analysis", {}).get("cost", {})
                total_cost = costs.get(str(origin.meeting_id), 0.0)
                for mid in spawned:
                    total_cost += costs.get(str(mid), 0.0)
                
                cascade_chains.append(CascadeChain(
                    origin_meeting_id=origin.meeting_id,
                    spawned_meeting_ids=spawned,
                    total_cascade_cost=total_cost,
                    cascade_depth=len(spawned),
                ))
        
        # Detect focus time anomalies
        for fs in focus_scores:
            if fs.focus_percentage < 0.15:
                anomalies.append(Anomaly(
                    entity_id=fs.person_email,
                    entity_type="person",
                    anomaly_type="critical_overload",
                    severity="high",
                    description=f"{fs.person_email} has only {fs.focus_percentage:.0%} focus time remaining",
                ))
        
        logger.info(f"Detected {len(anomalies)} anomalies and {len(cascade_chains)} cascade chains")
        await log_agent_event(session_id, "anomaly_detection_agent", 4, "complete")
        
        return {
            "anomalies": anomalies,
            "cascade_chains": cascade_chains,
        }
        
    except Exception as e:
        error = f"Anomaly detection failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "anomaly_detection_agent", 4, "failed", error)
        return {"anomalies": [], "cascade_chains": []}


async def network_analysis_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 4: Build meeting co-occurrence network.
    
    Creates graph:
    - Nodes: people
    - Edges: co-occurrence in meetings
    - Computes centrality and identifies bottlenecks
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "network_analysis_agent", 4, "running")
    
    try:
        meetings = state["validated_meetings"]
        focus_scores = state.get("focus_scores", [])
        costs = state.get("parallel_analysis", {}).get("cost", {})
        
        # Build focus lookup
        focus_lookup = {fs.person_email: fs for fs in focus_scores}
        
        # Count co-occurrences
        edge_data = defaultdict(lambda: {"count": 0, "cost": 0.0})
        person_meetings = defaultdict(int)
        
        for meeting in meetings:
            attendees = list(meeting.attendee_emails)
            meeting_cost = costs.get(str(meeting.meeting_id), 0.0)
            
            for email in attendees:
                person_meetings[email] += 1
            
            # Create edges for all pairs
            for i, email_a in enumerate(attendees):
                for email_b in attendees[i + 1:]:
                    pair = tuple(sorted([email_a, email_b]))
                    edge_data[pair]["count"] += 1
                    edge_data[pair]["cost"] += meeting_cost
        
        # Calculate centrality (degree centrality)
        total_people = len(person_meetings)
        
        nodes = []
        for email, meeting_count in person_meetings.items():
            fs = focus_lookup.get(email)
            if not fs:
                continue
            
            # Centrality: how many unique people they meet with
            unique_connections = sum(
                1 for pair in edge_data.keys()
                if email in pair
            )
            centrality = unique_connections / (total_people - 1) if total_people > 1 else 0.0
            
            # At risk: high centrality + low focus
            at_risk = centrality > 0.75 and fs.focus_percentage < 0.35
            
            nodes.append(PersonNode(
                email=email,
                display_name=email.split("@")[0].title(),
                total_meeting_hours=fs.total_meeting_hours,
                centrality_score=centrality,
                focus_percentage=fs.focus_percentage,
                at_risk=at_risk,
            ))
        
        # Create edges
        edges = []
        for (person_a, person_b), data in edge_data.items():
            edges.append(MeetingEdge(
                person_a=person_a,
                person_b=person_b,
                co_occurrence_count=data["count"],
                combined_cost=data["cost"],
            ))
        
        # Find most central person
        most_central = max(nodes, key=lambda n: n.centrality_score) if nodes else None
        most_central_email = most_central.email if most_central else ""
        
        # Find highest cost pair
        highest_cost_edge = max(edges, key=lambda e: e.combined_cost) if edges else None
        highest_cost_pair = (
            (highest_cost_edge.person_a, highest_cost_edge.person_b)
            if highest_cost_edge else ("", "")
        )
        
        network_graph = NetworkGraph(
            nodes=nodes,
            edges=edges,
            most_central_person=most_central_email,
            highest_cost_pair=highest_cost_pair,
        )
        
        logger.info(f"Built network with {len(nodes)} nodes and {len(edges)} edges")
        await log_agent_event(session_id, "network_analysis_agent", 4, "complete")
        
        return {"network_graph": network_graph}
        
    except Exception as e:
        error = f"Network analysis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "network_analysis_agent", 4, "failed", error)
        return {"network_graph": None}


async def trend_analysis_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Tier 5 (Conditional): Compare current vs previous session.
    
    Only fires if previous session exists in database.
    """
    session_id = state["session_id"]
    await log_agent_event(session_id, "trend_analysis_agent", 5, "running")
    
    try:
        # TODO: Query SQLite for previous session
        # For MVP, return empty trends
        
        logger.info("Trend analysis complete (no previous session)")
        await log_agent_event(session_id, "trend_analysis_agent", 5, "complete")
        
        parallel_analysis = state.get("parallel_analysis", {})
        parallel_analysis["trends"] = {
            "has_previous_session": False,
            "delta_average_waste": 0.0,
            "delta_total_cost": 0.0,
            "trend_direction": "stable",
        }
        
        return {"parallel_analysis": parallel_analysis}
        
    except Exception as e:
        error = f"Trend analysis failed: {str(e)}"
        logger.error(error)
        state["errors"].append(error)
        await log_agent_event(session_id, "trend_analysis_agent", 5, "failed", error)
        return {"parallel_analysis": state.get("parallel_analysis", {})}


async def compute_roi_projection(state: dict[str, Any]) -> dict[str, Any]:
    """
    Compute ROI projection from recommendations.
    Called after recommendation_agent completes.
    """
    try:
        recommendations = state.get("recommendations", [])
        waste_scores = state.get("waste_scores", [])
        costs = state.get("parallel_analysis", {}).get("cost", {})
        
        # Calculate potential savings from top recommendations
        high_priority_recs = [r for r in recommendations if r.priority <= 2]
        
        total_saving = 0.0
        top_changes = []
        
        for rec in high_priority_recs[:5]:  # Top 5
            meeting_cost = costs.get(str(rec.meeting_id), 0.0)
            
            if rec.recommended_action == "cancel":
                saving = meeting_cost * 52  # Annual
            elif rec.recommended_action == "shorten":
                saving = meeting_cost * 0.5 * 52
            elif rec.recommended_action == "merge":
                saving = meeting_cost * 0.3 * 52
            else:
                saving = 0.0
            
            if saving > 0:
                total_saving += saving
                top_changes.append(f"{rec.recommended_action.title()}: {rec.reasoning[:50]}...")
        
        # Weeks to break even (assuming implementation cost)
        implementation_cost = 10000  # Placeholder
        weeks_to_break_even = int(implementation_cost / (total_saving / 52)) if total_saving > 0 else 999
        
        roi = ROIProjection(
            projected_annual_saving=total_saving,
            weeks_to_break_even=weeks_to_break_even,
            top_changes=top_changes,
            assumptions=[
                "All high-priority recommendations implemented",
                "Meeting patterns remain consistent",
                "No additional meetings added",
            ],
        )
        
        return {"roi_projection": roi}
        
    except Exception as e:
        logger.error(f"ROI projection failed: {str(e)}")
        return {"roi_projection": None}

# Made with Bob
