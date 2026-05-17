"""
5-node LangGraph analysis pipeline.
Replaces the old 19-agent, 6-tier graph with a clean linear 5-node design.
Only 2 LLM calls in the entire pipeline (extract_node + synthesize_node).
"""
import json
import logging
from typing import Any

import aiosqlite
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.graph.state import AnalysisState
from app.graph.nodes.tools import (
    classify_meetings,
    compute_costs,
    analyze_participation,
    analyze_recurrence,
    compute_waste_scores,
    compute_focus_scores,
    compute_health_scores,
    detect_cascades_anomalies,
    build_network,
    compute_recommendations,
    compute_interventions,
    compute_roi,
)
from app.graph.nodes.llm_nodes import extract_insights_node, synthesize_report_node
from app.utils.agent_logger import log_agent_event
from app.utils.csv_parser import parse_csv

logger = logging.getLogger(__name__)

# Agent name → tier mapping for the 5-node pipeline
PIPELINE_AGENTS = [
    ("ingest_agent", 1),
    ("analyze_agent", 2),
    ("extract_agent", 3),
    ("synthesize_agent", 4),
    ("save_agent", 5),
]


# ============================================================================
# Node 1: ingest_node
# ============================================================================

async def ingest_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Parse historical CSV (+ optional upcoming CSV).
    Parse transcripts dict from uploaded_files.
    Validate meetings and emit ingest_agent event.
    """
    session_id = state["session_id"]
    uploaded_files: dict[str, str] = state.get("uploaded_files", {})
    config: dict[str, Any] = state.get("config", {})
    errors: list[str] = list(state.get("errors", []))

    await log_agent_event(session_id, "ingest_agent", 1, "running")

    try:
        # --- Parse historical CSV ---
        historical_content = uploaded_files.get("historical_csv", "")
        if not historical_content:
            error = "No historical CSV uploaded"
            errors.append(error)
            await log_agent_event(session_id, "ingest_agent", 1, "failed", error)
            return {"errors": errors, "validated_meetings": [], "transcripts": {}}

        meetings, parse_errors = parse_csv(historical_content)
        errors.extend(parse_errors)

        if not meetings:
            error = "No valid meetings parsed from CSV"
            errors.append(error)
            await log_agent_event(session_id, "ingest_agent", 1, "failed", error)
            return {"errors": errors, "validated_meetings": [], "transcripts": {}}

        # --- Parse upcoming CSV (optional) ---
        upcoming_content = uploaded_files.get("upcoming_csv", "")
        upcoming_meetings = []
        if upcoming_content:
            upcoming_meetings, upcoming_errors = parse_csv(upcoming_content)
            errors.extend(upcoming_errors)
            logger.info(f"ingest_node: parsed {len(upcoming_meetings)} upcoming meetings")

        # --- Parse transcripts ---
        # uploaded_files may contain "transcript_{index}" → text, keyed by meeting index
        # We need to match by index to meetings list
        transcripts: dict[str, str] = {}
        for key, value in uploaded_files.items():
            if key.startswith("transcript_"):
                try:
                    idx = int(key.split("_", 1)[1])
                    if 0 <= idx < len(meetings):
                        mid = str(meetings[idx].meeting_id)
                        transcripts[mid] = value
                except (ValueError, IndexError):
                    pass

        logger.info(
            f"ingest_node: {len(meetings)} meetings, {len(transcripts)} transcripts, "
            f"{len(upcoming_meetings)} upcoming"
        )

        await log_agent_event(session_id, "ingest_agent", 1, "complete")

        return {
            "validated_meetings": meetings,
            "transcripts": transcripts,
            "upcoming_risks": [],  # filled later if needed
            "errors": errors,
        }

    except Exception as e:
        error = f"ingest_node failed: {str(e)}"
        logger.error(error)
        errors.append(error)
        await log_agent_event(session_id, "ingest_agent", 1, "failed", error)
        return {"errors": errors, "validated_meetings": [], "transcripts": {}}


# ============================================================================
# Node 2: analyze_node
# ============================================================================

async def analyze_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    All algorithmic analysis in one node — no LLM.
    Calls all tool functions from tools.py and populates state.
    """
    session_id = state["session_id"]
    meetings = state.get("validated_meetings", [])
    config: dict[str, Any] = state.get("config", {})
    errors: list[str] = list(state.get("errors", []))

    await log_agent_event(session_id, "analyze_agent", 2, "running")

    if not meetings:
        await log_agent_event(session_id, "analyze_agent", 2, "failed", "No meetings to analyse")
        return {"errors": errors}

    try:
        hourly_rate = float(config.get("hourly_rate", settings.DEFAULT_HOURLY_RATE))

        # Run all algorithmic tools in order (no LLM, no async needed)
        meeting_classifications = classify_meetings(meetings)
        costs = compute_costs(meetings, hourly_rate)

        participation = analyze_participation(meetings, meeting_classifications)
        recurrence = analyze_recurrence(meetings)

        # decisions dict is empty at this stage — filled by extract_node
        # compute_waste_scores accepts it empty and will use notes-based heuristics
        decisions: dict[str, list[str]] = {}

        waste_scores = compute_waste_scores(
            meetings, meeting_classifications, costs, decisions,
            participation, recurrence, config
        )
        focus_scores = compute_focus_scores(meetings)
        meeting_health_scores = compute_health_scores(meetings, meeting_classifications)
        cascade_chains, anomalies = detect_cascades_anomalies(meetings, waste_scores, costs, focus_scores)
        network_graph = build_network(meetings, focus_scores, costs)
        recommendations = compute_recommendations(
            waste_scores, meetings, meeting_classifications, recurrence
        )
        interventions = compute_interventions(waste_scores, meetings, meeting_classifications)
        meeting_titles = {str(m.meeting_id): m.title for m in meetings}
        roi_projection = compute_roi(waste_scores, recommendations, costs, meeting_titles)

        logger.info(
            f"analyze_node: {len(meeting_classifications)} classifications, "
            f"{len(waste_scores)} waste scores, {len(focus_scores)} focus scores, "
            f"{len(anomalies)} anomalies, {len(cascade_chains)} cascade chains"
        )

        await log_agent_event(session_id, "analyze_agent", 2, "complete")

        return {
            "meeting_classifications": meeting_classifications,
            "costs": costs,
            "waste_scores": waste_scores,
            "focus_scores": focus_scores,
            "meeting_health_scores": meeting_health_scores,
            "anomalies": anomalies,
            "cascade_chains": cascade_chains,
            "network_graph": network_graph,
            "recommendations": recommendations,
            "interventions": interventions,
            "roi_projection": roi_projection,
            "errors": errors,
        }

    except Exception as e:
        error = f"analyze_node failed: {str(e)}"
        logger.error(error, exc_info=True)
        errors.append(error)
        await log_agent_event(session_id, "analyze_agent", 2, "failed", error)
        return {"errors": errors}


# ============================================================================
# Node 3: extract_node
# ============================================================================

async def extract_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    ONE LLM call — extract action items + decisions from all meetings with notes/transcripts.
    After extraction, recompute waste_scores with real decision data for better accuracy.
    """
    session_id = state["session_id"]
    errors: list[str] = list(state.get("errors", []))

    await log_agent_event(session_id, "extract_agent", 3, "running")

    try:
        result = await extract_insights_node(state)
        action_items = result.get("action_items", [])
        decisions: dict[str, list[str]] = result.get("decisions", {})

        # Recompute waste scores now that we have real decision data
        meetings = state.get("validated_meetings", [])
        meeting_classifications = state.get("meeting_classifications", [])
        costs = state.get("costs", {})

        # Recompute with real decision data for more accurate waste scores
        if meetings and meeting_classifications:
            participation = analyze_participation(meetings, meeting_classifications)
            recurrence = analyze_recurrence(meetings)
            config = state.get("config", {})
            updated_waste_scores = compute_waste_scores(
                meetings, meeting_classifications, costs, decisions,
                participation, recurrence, config
            )
        else:
            updated_waste_scores = state.get("waste_scores", [])

        await log_agent_event(session_id, "extract_agent", 3, "complete")

        return {
            "action_items": action_items,
            "decisions": decisions,
            "waste_scores": updated_waste_scores,
            "errors": errors,
        }

    except Exception as e:
        error = f"extract_node failed: {str(e)}"
        logger.error(error, exc_info=True)
        errors.append(error)
        await log_agent_event(session_id, "extract_agent", 3, "failed", error)
        return {
            "action_items": [],
            "decisions": {},
            "errors": errors,
        }


# ============================================================================
# Node 4: synthesize_node
# ============================================================================

async def synthesize_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    ONE LLM call — generate executive report using compact summary of all analysis.
    """
    session_id = state["session_id"]
    errors: list[str] = list(state.get("errors", []))

    await log_agent_event(session_id, "synthesize_agent", 4, "running")

    try:
        result = await synthesize_report_node(state)
        await log_agent_event(session_id, "synthesize_agent", 4, "complete")
        return {**result, "errors": errors}

    except Exception as e:
        error = f"synthesize_node failed: {str(e)}"
        logger.error(error, exc_info=True)
        errors.append(error)
        await log_agent_event(session_id, "synthesize_agent", 4, "failed", error)
        return {"executive_report": None, "errors": errors}


# ============================================================================
# Node 5: save_node
# ============================================================================

async def save_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Write EVERYTHING to DB (all tables). Mark session complete.
    """
    session_id = state["session_id"]
    errors: list[str] = list(state.get("errors", []))

    await log_agent_event(session_id, "save_agent", 5, "running")

    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:

            # --- Meetings ---
            for meeting in state.get("validated_meetings", []):
                await db.execute(
                    """
                    INSERT OR REPLACE INTO meetings
                    (meeting_id, session_id, title, start_datetime, end_datetime,
                     duration_minutes, attendee_emails, organizer_email, is_recurring,
                     recurrence_rule, meeting_type, notes_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(meeting.meeting_id),
                        session_id,
                        meeting.title,
                        meeting.start_datetime.isoformat(),
                        meeting.end_datetime.isoformat(),
                        meeting.duration_minutes,
                        json.dumps([str(e) for e in meeting.attendee_emails]),
                        str(meeting.organizer_email) if meeting.organizer_email else None,
                        int(meeting.is_recurring),
                        meeting.recurrence_rule,
                        meeting.meeting_type,
                        meeting.notes_text,
                    ),
                )

            # --- Meeting classifications ---
            for mc in state.get("meeting_classifications", []):
                await db.execute(
                    """
                    INSERT OR REPLACE INTO meeting_classifications
                    (meeting_id, session_id, meeting_type, confidence)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(mc.meeting_id), session_id, mc.meeting_type, mc.confidence),
                )

            # --- Waste scores ---
            for ws in state.get("waste_scores", []):
                await db.execute(
                    """
                    INSERT INTO waste_scores
                    (meeting_id, session_id, cost_factor, decision_deficit,
                     participation_imbalance, recurrence_staleness, composite_score,
                     category, threshold_exceeded)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(ws.meeting_id),
                        session_id,
                        ws.cost_factor,
                        ws.decision_deficit,
                        ws.participation_imbalance,
                        ws.recurrence_staleness,
                        ws.composite_score,
                        ws.category,
                        int(ws.threshold_exceeded),
                    ),
                )

            # --- Recommendations ---
            for rec in state.get("recommendations", []):
                await db.execute(
                    """
                    INSERT INTO recommendations
                    (meeting_id, session_id, recommended_action, reasoning, priority)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(rec.meeting_id),
                        session_id,
                        rec.recommended_action,
                        rec.reasoning,
                        rec.priority,
                    ),
                )

            # --- Focus scores ---
            for fs in state.get("focus_scores", []):
                await db.execute(
                    """
                    INSERT INTO focus_scores
                    (session_id, person_email, total_meeting_hours, focus_blocks_remaining,
                     longest_focus_block_minutes, focus_percentage)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        fs.person_email,
                        fs.total_meeting_hours,
                        fs.focus_blocks_remaining,
                        fs.longest_focus_block_minutes,
                        fs.focus_percentage,
                    ),
                )

            # --- Meeting health scores ---
            for mh in state.get("meeting_health_scores", []):
                await db.execute(
                    """
                    INSERT INTO meeting_health_scores
                    (meeting_id, session_id, has_agenda, duration_appropriate,
                     attendee_fit_score, overall_health_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(mh.meeting_id),
                        session_id,
                        int(mh.has_agenda),
                        int(mh.duration_appropriate),
                        mh.attendee_fit_score,
                        mh.overall_health_score,
                    ),
                )

            # --- Action items ---
            for ai in state.get("action_items", []):
                await db.execute(
                    """
                    INSERT INTO action_items
                    (meeting_id, session_id, description, assignee_email, followed_through)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(ai.meeting_id),
                        session_id,
                        ai.description,
                        ai.assignee_email,
                        int(ai.followed_through) if ai.followed_through is not None else None,
                    ),
                )

            # --- Anomalies ---
            for anomaly in state.get("anomalies", []):
                await db.execute(
                    """
                    INSERT INTO anomalies
                    (session_id, entity_id, entity_type, anomaly_type, severity, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        anomaly.entity_id,
                        anomaly.entity_type,
                        anomaly.anomaly_type,
                        anomaly.severity,
                        anomaly.description,
                    ),
                )

            # --- Cascade chains ---
            for chain in state.get("cascade_chains", []):
                cursor = await db.execute(
                    """
                    INSERT INTO cascade_chains
                    (session_id, origin_meeting_id, total_cascade_cost, cascade_depth)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        str(chain.origin_meeting_id),
                        chain.total_cascade_cost,
                        chain.cascade_depth,
                    ),
                )
                chain_id = cursor.lastrowid
                for spawned_id in chain.spawned_meeting_ids:
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO cascade_chain_meetings (chain_id, meeting_id)
                        VALUES (?, ?)
                        """,
                        (chain_id, str(spawned_id)),
                    )

            # --- Network graph ---
            network = state.get("network_graph")
            if network:
                for node in network.nodes:
                    await db.execute(
                        """
                        INSERT INTO network_nodes
                        (session_id, email, display_name, total_meeting_hours,
                         centrality_score, focus_percentage, at_risk)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            node.email,
                            node.display_name,
                            node.total_meeting_hours,
                            node.centrality_score,
                            node.focus_percentage,
                            int(node.at_risk),
                        ),
                    )
                for edge in network.edges:
                    await db.execute(
                        """
                        INSERT INTO network_edges
                        (session_id, person_a, person_b, co_occurrence_count, combined_cost)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            edge.person_a,
                            edge.person_b,
                            edge.co_occurrence_count,
                            edge.combined_cost,
                        ),
                    )

            # --- Interventions ---
            for intervention in state.get("interventions", []):
                await db.execute(
                    """
                    INSERT INTO interventions
                    (meeting_id, session_id, pre_meeting_email_template, suggested_agenda,
                     recommended_attendee_reduction, alternative_format)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(intervention.meeting_id),
                        session_id,
                        intervention.pre_meeting_email_template,
                        json.dumps(intervention.suggested_agenda),
                        json.dumps([str(e) for e in intervention.recommended_attendee_reduction]),
                        intervention.alternative_format,
                    ),
                )

            # --- Transcripts ---
            transcripts: dict[str, str] = state.get("transcripts", {})
            for meeting_id_str, content in transcripts.items():
                await db.execute(
                    """
                    INSERT OR REPLACE INTO transcripts (meeting_id, session_id, content)
                    VALUES (?, ?, ?)
                    """,
                    (meeting_id_str, session_id, content),
                )

            # --- Executive report ---
            report = state.get("executive_report")
            if report:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO reports
                    (session_id, period, total_cost, total_meetings, meetrix_score,
                     summary, key_findings, top_recommendations, trend_direction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        report.period,
                        report.total_cost,
                        report.total_meetings,
                        report.meetrix_score,
                        report.summary,
                        json.dumps(report.key_findings),
                        json.dumps(report.top_recommendations),
                        report.trend_direction,
                    ),
                )

            # --- ROI projection ---
            roi = state.get("roi_projection")
            if roi:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO roi_projections
                    (session_id, projected_annual_saving, weeks_to_break_even,
                     top_changes, assumptions)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        roi.projected_annual_saving,
                        roi.weeks_to_break_even,
                        json.dumps(roi.top_changes),
                        json.dumps(roi.assumptions),
                    ),
                )

            # --- Mark session complete ---
            await db.execute(
                """
                UPDATE sessions
                SET status = 'complete', completed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (session_id,),
            )

            await db.commit()

        logger.info(f"save_node: all results written for session {session_id}")
        await log_agent_event(session_id, "save_agent", 5, "complete")
        return {"errors": errors}

    except Exception as e:
        error = f"save_node failed: {str(e)}"
        logger.error(error, exc_info=True)
        errors.append(error)
        await log_agent_event(session_id, "save_agent", 5, "failed", error)

        # Mark session as failed
        try:
            async with aiosqlite.connect(settings.DATABASE_PATH) as db:
                await db.execute(
                    """
                    UPDATE sessions
                    SET status = 'failed', error_message = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                    """,
                    (error, session_id),
                )
                await db.commit()
        except Exception:
            pass

        return {"errors": errors}


# ============================================================================
# Graph builder
# ============================================================================

def build_analysis_graph():
    """
    Build and compile the 5-node analysis pipeline graph.
    Linear: ingest -> analyze -> extract -> synthesize -> save -> END
    Only 2 LLM calls total (extract + synthesize nodes).
    """
    builder = StateGraph(AnalysisState)

    builder.add_node("ingest", ingest_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("extract", extract_node)
    builder.add_node("synthesize", synthesize_node)
    builder.add_node("save", save_node)

    builder.set_entry_point("ingest")
    builder.add_edge("ingest", "analyze")
    builder.add_edge("analyze", "extract")
    builder.add_edge("extract", "synthesize")
    builder.add_edge("synthesize", "save")
    builder.add_edge("save", END)

    graph = builder.compile(checkpointer=MemorySaver())
    logger.info("Analysis graph compiled (5 nodes, 2 LLM calls)")
    return graph

# Made with Bob
