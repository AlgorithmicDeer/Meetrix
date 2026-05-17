"""
FastAPI routes for Meetrix API.
All 6 endpoints defined in implementation.md.
"""
import logging
from uuid import uuid4
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from typing import Any
import aiosqlite
import json
from app.models.schemas import (
    AnalysisResponse,
    AgentEvent,
    InsightRequest,
    InsightResponse,
    MeetingPreview,
    MeetingInfo,
    ScheduleRequest,
    MeetingProposal,
    SummaryStats,
    WasteScore,
    MeetingClassification,
    Recommendation,
    FocusTimeScore,
    MeetingHealth,
    ActionItem,
    Anomaly,
    CascadeChain,
    NetworkGraph,
    PersonNode,
    MeetingEdge,
    UpcomingRisk,
    Intervention,
    ExecutiveReport,
    ROIProjection,
)
from app.config import settings
from app.utils.agent_logger import initialize_agent_events
from app.utils.csv_parser import parse_csv

router = APIRouter()
logger = logging.getLogger(__name__)


# 5-node pipeline agent list (matches analysis_builder.py PIPELINE_AGENTS)
PIPELINE_AGENTS = [
    ("ingest_agent", 1),
    ("analyze_agent", 2),
    ("extract_agent", 3),
    ("synthesize_agent", 4),
    ("save_agent", 5),
]


async def run_analysis_pipeline(
    session_id: str,
    uploaded_files: dict[str, str],
    config: dict[str, Any],
    graph: Any,
):
    """
    Background task to run analysis pipeline.
    
    Args:
        session_id: Session identifier
        uploaded_files: Dict of filename → content
        config: Analysis configuration
        graph: Compiled analysis graph
    """
    try:
        # Initialize agent events
        await initialize_agent_events(session_id, PIPELINE_AGENTS)
        
        # Prepare initial state for the 5-node pipeline
        initial_state = {
            "session_id": session_id,
            "uploaded_files": uploaded_files,
            "config": config,
            "transcripts": {},
            "validated_meetings": [],
            "meeting_classifications": [],
            "costs": {},
            "waste_scores": [],
            "focus_scores": [],
            "meeting_health_scores": [],
            "action_items": [],
            "decisions": {},
            "anomalies": [],
            "cascade_chains": [],
            "network_graph": None,
            "upcoming_risks": [],
            "recommendations": [],
            "interventions": [],
            "executive_report": None,
            "roi_projection": None,
            "errors": [],
        }
        
        # Run graph
        await graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}},
        )
        
        logger.info(f"Analysis pipeline completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed for session {session_id}: {e}")
        
        # Mark session as failed
        try:
            async with aiosqlite.connect(settings.DATABASE_PATH) as db:
                await db.execute(
                    """
                    UPDATE sessions 
                    SET status = 'failed', error_message = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                    """,
                    (str(e), session_id),
                )
                await db.commit()
        except Exception:
            pass


@router.post("/parse-preview")
async def parse_preview(
    historical_csv: UploadFile = File(...),
) -> list[MeetingPreview]:
    """
    Parse CSV and return a lightweight meeting list for transcript-association UI.
    No DB writes — purely stateless parsing for the upload wizard.
    """
    try:
        content = (await historical_csv.read()).decode("utf-8")
        meetings, errors = parse_csv(content)
        if errors and not meetings:
            raise HTTPException(status_code=422, detail={"parse_errors": errors})
        return [
            MeetingPreview(
                index=i,
                title=m.title,
                start_datetime=m.start_datetime,
                duration_minutes=m.duration_minutes,
                attendee_count=len(m.attendee_emails),
                is_recurring=m.is_recurring,
            )
            for i, m in enumerate(meetings)
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"parse-preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_calendar(
    request: Request,
    background_tasks: BackgroundTasks,
    historical_csv: UploadFile = File(...),
    upcoming_csv: UploadFile | None = File(None),
    config: str = Form(...),
    transcripts_json: str = Form("{}"),
):
    """
    Upload calendar data (+ optional transcripts) and trigger analysis pipeline.

    transcripts_json: JSON string mapping meeting_index (int) to transcript text (str).
    Example: {"0": "Meeting transcript text...", "3": "Another transcript..."}

    Returns session_id immediately; pipeline runs in background.
    """
    try:
        # Parse config
        config_dict = json.loads(config)

        # Read uploaded files
        uploaded_files: dict[str, str] = {
            "historical_csv": (await historical_csv.read()).decode("utf-8"),
        }

        if upcoming_csv:
            uploaded_files["upcoming_csv"] = (await upcoming_csv.read()).decode("utf-8")

        # Parse and inject transcript files
        # transcripts_json: {meeting_index_str: transcript_text}
        try:
            transcripts_raw: dict[str, str] = json.loads(transcripts_json)
        except (json.JSONDecodeError, TypeError):
            transcripts_raw = {}

        for idx_str, text in transcripts_raw.items():
            try:
                idx = int(idx_str)
                if isinstance(text, str) and text.strip():
                    uploaded_files[f"transcript_{idx}"] = text.strip()
            except (ValueError, TypeError):
                pass

        # Generate session ID
        session_id = str(uuid4())

        # Create session in database
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            await db.execute(
                """
                INSERT INTO sessions (session_id, status)
                VALUES (?, 'processing')
                """,
                (session_id,),
            )
            await db.commit()

        # Get graph from app state (compiled at startup)
        graph = request.app.state.analysis_graph

        # Trigger background task
        background_tasks.add_task(
            run_analysis_pipeline,
            session_id,
            uploaded_files,
            config_dict,
            graph,
        )

        return {"session_id": session_id}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid config JSON")
    except Exception as e:
        logger.error(f"Analysis upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{session_id}")
async def get_results(session_id: str) -> AnalysisResponse:
    """
    Retrieve analysis results for a session.
    Frontend polls this endpoint every 3 seconds.
    """
    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            # Get session status
            cursor = await db.execute(
                "SELECT status, error_message FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            row = await cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Session not found")
            
            status, error_message = row
            
            # If still processing, return partial results
            if status == "processing":
                return AnalysisResponse(
                    session_id=session_id,
                    status="processing",
                    summary_stats=SummaryStats(
                        total_meetings=0,
                        total_cost=0.0,
                        average_waste_score=0.0,
                        high_waste_count=0,
                        meetrix_score=0,
                        people_in_overload=0,
                        cascade_chains_count=0,
                        upcoming_risks_count=0,
                    ),
                )
            
            if status == "failed":
                return AnalysisResponse(
                    session_id=session_id,
                    status="failed",
                    error_message=error_message,
                    summary_stats=SummaryStats(
                        total_meetings=0,
                        total_cost=0.0,
                        average_waste_score=0.0,
                        high_waste_count=0,
                        meetrix_score=0,
                        people_in_overload=0,
                        cascade_chains_count=0,
                        upcoming_risks_count=0,
                    ),
                )
            
            # Status is "complete" — read real results from database
            cursor = await db.execute(
                "SELECT COUNT(*) FROM meetings WHERE session_id = ?", (session_id,)
            )
            total_meetings = (await cursor.fetchone())[0]

            cursor = await db.execute(
                """SELECT AVG(composite_score), SUM(CASE WHEN threshold_exceeded=1 THEN 1 ELSE 0 END)
                   FROM waste_scores WHERE session_id = ?""",
                (session_id,),
            )
            row = await cursor.fetchone()
            avg_waste = row[0] or 0.0
            high_waste_count = row[1] or 0

            cursor = await db.execute(
                "SELECT meetrix_score, total_cost FROM reports WHERE session_id = ?",
                (session_id,),
            )
            report_row = await cursor.fetchone()
            meetrix_score = int(report_row[0]) if report_row else 0
            total_cost = float(report_row[1]) if report_row else 0.0

            cursor = await db.execute(
                "SELECT COUNT(*) FROM focus_scores WHERE session_id = ? AND total_meeting_hours > 15",
                (session_id,),
            )
            people_in_overload = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(*) FROM cascade_chains WHERE session_id = ?", (session_id,)
            )
            cascade_chains_count = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(*) FROM upcoming_risks WHERE session_id = ?", (session_id,)
            )
            upcoming_risks_count = (await cursor.fetchone())[0]

            # --- Read all detailed results ---

            # Meetings (for title display in frontend)
            cursor = await db.execute(
                """SELECT meeting_id, title, start_datetime, duration_minutes,
                   attendee_emails, is_recurring, meeting_type
                   FROM meetings WHERE session_id = ? ORDER BY start_datetime""",
                (session_id,),
            )
            meeting_rows = await cursor.fetchall()
            meetings_data = []
            for r in meeting_rows:
                try:
                    attendee_emails = json.loads(r[4]) if r[4] else []
                    attendee_count = len(attendee_emails)
                except (json.JSONDecodeError, TypeError):
                    attendee_count = 0
                meetings_data.append(MeetingInfo(
                    meeting_id=r[0],
                    title=r[1],
                    start_datetime=str(r[2]),
                    duration_minutes=r[3],
                    attendee_count=attendee_count,
                    is_recurring=bool(r[5]),
                    meeting_type=r[6],
                ))

            # Waste scores
            cursor = await db.execute(
                """SELECT meeting_id, cost_factor, decision_deficit, participation_imbalance,
                   recurrence_staleness, composite_score, category, threshold_exceeded
                   FROM waste_scores WHERE session_id = ?""",
                (session_id,),
            )
            waste_scores_rows = await cursor.fetchall()
            waste_scores_data = [
                WasteScore(
                    meeting_id=r[0], cost_factor=r[1] or 0.0, decision_deficit=r[2] or 0.0,
                    participation_imbalance=r[3] or 0.0, recurrence_staleness=r[4] or 0.0,
                    composite_score=r[5], category=r[6], threshold_exceeded=bool(r[7]),
                ) for r in waste_scores_rows
            ]

            # Meeting classifications
            cursor = await db.execute(
                "SELECT meeting_id, meeting_type, confidence FROM meeting_classifications WHERE session_id = ?",
                (session_id,),
            )
            mc_rows = await cursor.fetchall()
            meeting_classifications_data = [
                MeetingClassification(meeting_id=r[0], meeting_type=r[1], confidence=r[2])
                for r in mc_rows
            ]

            # Recommendations
            cursor = await db.execute(
                """SELECT meeting_id, recommended_action, reasoning, priority
                   FROM recommendations WHERE session_id = ? ORDER BY priority""",
                (session_id,),
            )
            rec_rows = await cursor.fetchall()
            recommendations_data = [
                Recommendation(
                    meeting_id=r[0], recommended_action=r[1], reasoning=r[2], priority=r[3]
                ) for r in rec_rows
            ]

            # Focus scores
            cursor = await db.execute(
                """SELECT person_email, total_meeting_hours, focus_blocks_remaining,
                   longest_focus_block_minutes, focus_percentage
                   FROM focus_scores WHERE session_id = ? ORDER BY focus_percentage""",
                (session_id,),
            )
            fs_rows = await cursor.fetchall()
            focus_scores_data = [
                FocusTimeScore(
                    person_email=r[0], total_meeting_hours=r[1] or 0.0,
                    focus_blocks_remaining=r[2] or 0, longest_focus_block_minutes=r[3] or 0,
                    focus_percentage=r[4] or 0.0,
                ) for r in fs_rows
            ]

            # Meeting health scores
            cursor = await db.execute(
                """SELECT meeting_id, has_agenda, duration_appropriate,
                   attendee_fit_score, overall_health_score
                   FROM meeting_health_scores WHERE session_id = ?""",
                (session_id,),
            )
            mh_rows = await cursor.fetchall()
            health_scores_data = [
                MeetingHealth(
                    meeting_id=r[0], has_agenda=bool(r[1]), duration_appropriate=bool(r[2]),
                    attendee_fit_score=r[3] or 0.0, overall_health_score=r[4] or 0.0,
                ) for r in mh_rows
            ]

            # Action items
            cursor = await db.execute(
                """SELECT meeting_id, description, assignee_email, followed_through
                   FROM action_items WHERE session_id = ?""",
                (session_id,),
            )
            ai_rows = await cursor.fetchall()
            action_items_data = [
                ActionItem(
                    meeting_id=r[0], description=r[1],
                    assignee_email=r[2], followed_through=bool(r[3]) if r[3] is not None else None,
                ) for r in ai_rows
            ]

            # Anomalies
            cursor = await db.execute(
                """SELECT entity_id, entity_type, anomaly_type, severity, description
                   FROM anomalies WHERE session_id = ?""",
                (session_id,),
            )
            an_rows = await cursor.fetchall()
            anomalies_data = [
                Anomaly(
                    entity_id=r[0], entity_type=r[1], anomaly_type=r[2],
                    severity=r[3], description=r[4],
                ) for r in an_rows
            ]

            # Cascade chains
            cursor = await db.execute(
                """SELECT id, origin_meeting_id, total_cascade_cost, cascade_depth
                   FROM cascade_chains WHERE session_id = ? ORDER BY total_cascade_cost DESC""",
                (session_id,),
            )
            cc_rows = await cursor.fetchall()
            cascade_chains_data = []
            for cc_row in cc_rows:
                cursor2 = await db.execute(
                    "SELECT meeting_id FROM cascade_chain_meetings WHERE chain_id = ?",
                    (cc_row[0],),
                )
                spawned = [r[0] for r in await cursor2.fetchall()]
                cascade_chains_data.append(CascadeChain(
                    origin_meeting_id=cc_row[1], spawned_meeting_ids=spawned,
                    total_cascade_cost=cc_row[2], cascade_depth=cc_row[3],
                ))

            # Network graph
            cursor = await db.execute(
                """SELECT email, display_name, total_meeting_hours, centrality_score,
                   focus_percentage, at_risk FROM network_nodes WHERE session_id = ?""",
                (session_id,),
            )
            node_rows = await cursor.fetchall()
            network_graph_data = None
            if node_rows:
                nodes = [
                    PersonNode(
                        email=r[0], display_name=r[1], total_meeting_hours=r[2] or 0.0,
                        centrality_score=r[3] or 0.0, focus_percentage=r[4] or 0.0,
                        at_risk=bool(r[5]),
                    ) for r in node_rows
                ]
                cursor = await db.execute(
                    """SELECT person_a, person_b, co_occurrence_count, combined_cost
                       FROM network_edges WHERE session_id = ? ORDER BY combined_cost DESC""",
                    (session_id,),
                )
                edge_rows = await cursor.fetchall()
                edges = [
                    MeetingEdge(
                        person_a=r[0], person_b=r[1],
                        co_occurrence_count=r[2], combined_cost=r[3],
                    ) for r in edge_rows
                ]
                most_central = max(nodes, key=lambda n: n.centrality_score).email if nodes else ""
                highest_cost_pair = (edges[0].person_a, edges[0].person_b) if edges else ("", "")
                network_graph_data = NetworkGraph(
                    nodes=nodes, edges=edges,
                    most_central_person=most_central,
                    highest_cost_pair=highest_cost_pair,
                )

            # Upcoming risks
            cursor = await db.execute(
                """SELECT meeting_id, title, scheduled_datetime, attendee_emails,
                   waste_probability, risk_factors, recommended_intervention
                   FROM upcoming_risks WHERE session_id = ? ORDER BY waste_probability DESC""",
                (session_id,),
            )
            ur_rows = await cursor.fetchall()
            upcoming_risks_data = [
                UpcomingRisk(
                    upcoming_meeting_id=r[0], title=r[1], scheduled_datetime=r[2],
                    attendee_emails=json.loads(r[3]),
                    waste_probability=r[4], risk_factors=json.loads(r[5]),
                    recommended_intervention=r[6],
                ) for r in ur_rows
            ]

            # Interventions
            cursor = await db.execute(
                """SELECT meeting_id, pre_meeting_email_template, suggested_agenda,
                   recommended_attendee_reduction, alternative_format
                   FROM interventions WHERE session_id = ?""",
                (session_id,),
            )
            iv_rows = await cursor.fetchall()
            interventions_data = [
                Intervention(
                    meeting_id=r[0], pre_meeting_email_template=r[1],
                    suggested_agenda=json.loads(r[2]),
                    recommended_attendee_reduction=json.loads(r[3]),
                    alternative_format=r[4],
                ) for r in iv_rows
            ]

            # Executive report
            cursor = await db.execute(
                """SELECT period, total_cost, total_meetings, meetrix_score, summary,
                   key_findings, top_recommendations, trend_direction, data_residency
                   FROM reports WHERE session_id = ?""",
                (session_id,),
            )
            rpt_row = await cursor.fetchone()
            executive_report_data = None
            if rpt_row:
                executive_report_data = ExecutiveReport(
                    period=rpt_row[0], total_cost=rpt_row[1] or 0.0,
                    total_meetings=rpt_row[2] or 0, meetrix_score=int(rpt_row[3]),
                    summary=rpt_row[4] or "",
                    key_findings=json.loads(rpt_row[5]) if rpt_row[5] else [],
                    top_recommendations=json.loads(rpt_row[6]) if rpt_row[6] else [],
                    trend_direction=rpt_row[7] or "stable",
                    data_residency=rpt_row[8] or "All data processed locally.",
                )

            # ROI projection
            cursor = await db.execute(
                """SELECT projected_annual_saving, weeks_to_break_even, top_changes, assumptions
                   FROM roi_projections WHERE session_id = ?""",
                (session_id,),
            )
            roi_row = await cursor.fetchone()
            roi_projection_data = None
            if roi_row:
                roi_projection_data = ROIProjection(
                    projected_annual_saving=roi_row[0],
                    weeks_to_break_even=roi_row[1],
                    top_changes=json.loads(roi_row[2]) if roi_row[2] else [],
                    assumptions=json.loads(roi_row[3]) if roi_row[3] else [],
                )

            return AnalysisResponse(
                session_id=session_id,
                status="complete",
                summary_stats=SummaryStats(
                    total_meetings=total_meetings,
                    total_cost=total_cost,
                    average_waste_score=avg_waste,
                    high_waste_count=high_waste_count,
                    meetrix_score=meetrix_score,
                    people_in_overload=people_in_overload,
                    cascade_chains_count=cascade_chains_count,
                    upcoming_risks_count=upcoming_risks_count,
                ),
                meetings=meetings_data,
                waste_scores=waste_scores_data,
                meeting_classifications=meeting_classifications_data,
                recommendations=recommendations_data,
                focus_scores=focus_scores_data,
                meeting_health_scores=health_scores_data,
                action_items=action_items_data,
                anomalies=anomalies_data,
                cascade_chains=cascade_chains_data,
                network_graph=network_graph_data,
                upcoming_risks=upcoming_risks_data,
                interventions=interventions_data,
                executive_report=executive_report_data,
                roi_projection=roi_projection_data,
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/agent-status")
async def get_agent_status(session_id: str):
    """
    Retrieve live agent execution status.
    Frontend polls this every 1 second during analysis.
    """
    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            cursor = await db.execute(
                """
                SELECT agent_name, tier, status, started_at, completed_at, error_message
                FROM agent_events
                WHERE session_id = ?
                ORDER BY tier, agent_name
                """,
                (session_id,),
            )
            rows = await cursor.fetchall()
            
            agents = []
            for row in rows:
                agents.append(AgentEvent(
                    agent_name=row[0],
                    tier=row[1],
                    status=row[2],
                    started_at=row[3],
                    completed_at=row[4],
                    error_message=row[5],
                ))
            
            return {"agents": agents}
            
    except Exception as e:
        logger.error(f"Failed to fetch agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights")
async def query_insights(insight_request: InsightRequest, request: Request) -> InsightResponse:
    """
    Ask natural language questions about stored analysis results.
    """
    try:
        graph = request.app.state.interaction_graph
        result = await graph.ainvoke(
            {
                "session_id": insight_request.session_id,
                "query": insight_request.query,
                "answer": None,
                "relevant_meeting_ids": [],
                "errors": [],
            },
            config={"configurable": {"thread_id": insight_request.session_id}},
        )
        return InsightResponse(
            answer=result.get("answer") or "No answer generated",
            relevant_meeting_ids=result.get("relevant_meeting_ids", []),
        )
    except Exception as e:
        logger.error(f"Insight query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_meeting(request: ScheduleRequest) -> MeetingProposal:
    """
    Generate intelligent meeting proposal with waste prediction.
    """
    # TODO: Implement with interaction graph
    raise HTTPException(status_code=501, detail="Scheduling feature coming soon")


@router.get("/health")
async def health_check():
    """
    Check service health and Ollama connectivity.
    """
    import httpx
    
    ollama_connected = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(settings.OLLAMA_BASE_URL)
            ollama_connected = r.status_code == 200
    except Exception:
        pass
    
    return {
        "status": "healthy" if ollama_connected else "degraded",
        "ollama_connected": ollama_connected,
        "ollama_url": settings.OLLAMA_BASE_URL,
        "privacy_summary": {
            "llm": "local",
            "storage": "local",
            "network_calls": "none",
        },
    }

# Made with Bob
