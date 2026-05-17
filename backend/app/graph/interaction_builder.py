"""
Interaction graph builder for insight queries and scheduling.
Separate compiled graph from analysis pipeline.
"""
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.state import InsightState, ScheduleState

logger = logging.getLogger(__name__)


async def insight_query_node(state: dict) -> dict:
    """
    Process natural language query with full analysis data as context.
    Builds a rich context including per-meeting costs, classifications, waste scores,
    action items, cascade chains, and focus scores.
    """
    from app.llm import get_llm
    from app.config import settings
    import aiosqlite
    import json as _json
    from langchain_core.messages import SystemMessage, HumanMessage

    session_id = state.get("session_id", "")
    query = state.get("query", "")

    context_parts: list[str] = []

    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            # 1. Executive report
            cursor = await db.execute(
                "SELECT summary, key_findings, top_recommendations, total_cost, total_meetings, meetrix_score "
                "FROM reports WHERE session_id = ?",
                (session_id,),
            )
            rpt = await cursor.fetchone()
            if rpt:
                context_parts.append(
                    f"OVERALL STATS: {rpt[4]} meetings, total cost ${rpt[3]:,.0f}, Meetrix Score {rpt[5]}/100\n"
                    f"SUMMARY: {rpt[0]}\n"
                    f"KEY FINDINGS: {rpt[1]}\n"
                    f"TOP RECOMMENDATIONS: {rpt[2]}"
                )

            # 2. Per-meeting cost breakdown (duration × attendees × $75/hr default)
            cursor = await db.execute(
                """SELECT m.title, m.duration_minutes, m.attendee_emails,
                          mc.meeting_type, ws.composite_score, ws.cost_factor,
                          ws.decision_deficit, ws.participation_imbalance, m.is_recurring,
                          m.meeting_id
                   FROM meetings m
                   LEFT JOIN meeting_classifications mc ON m.meeting_id = mc.meeting_id AND mc.session_id = ?
                   LEFT JOIN waste_scores ws ON m.meeting_id = ws.meeting_id AND ws.session_id = ?
                   WHERE m.session_id = ?
                   ORDER BY ws.composite_score DESC""",
                (session_id, session_id, session_id),
            )
            mtg_rows = await cursor.fetchall()

            if mtg_rows:
                lines = []
                for r in mtg_rows:
                    title, dur, att_json, mtype, waste, cost_f, dec_def, part_imb, recurring, mid = r
                    try:
                        att_count = len(_json.loads(att_json))
                    except Exception:
                        att_count = 0
                    cost_usd = (dur / 60) * att_count * 75  # $75/hr default
                    waste_str = f"waste={waste:.2f}" if waste is not None else "waste=n/a"
                    lines.append(
                        f'  "{title}" | type={mtype or "?"} | {dur}min | {att_count} people '
                        f'| cost=${cost_usd:.0f} | {waste_str} '
                        f'| recurring={"yes" if recurring else "no"} | id={mid}'
                    )
                context_parts.append("MEETINGS (sorted by waste score):\n" + "\n".join(lines))

            # 3. Focus scores
            cursor = await db.execute(
                "SELECT person_email, total_meeting_hours, focus_percentage "
                "FROM focus_scores WHERE session_id = ? ORDER BY focus_percentage",
                (session_id,),
            )
            focus_rows = await cursor.fetchall()
            if focus_rows:
                lines = [
                    f"  {r[0]}: {r[1]:.1f}hrs/wk in meetings, {r[2]*100:.0f}% focus time remaining"
                    + (" ⚠ OVERLOADED" if r[2] < 0.35 else "")
                    for r in focus_rows
                ]
                context_parts.append("PEOPLE / FOCUS TIME:\n" + "\n".join(lines))

            # 4. Action items
            cursor = await db.execute(
                """SELECT ai.description, ai.assignee_email, m.title
                   FROM action_items ai JOIN meetings m ON ai.meeting_id = m.meeting_id
                   WHERE ai.session_id = ?""",
                (session_id,),
            )
            ai_rows = await cursor.fetchall()
            if ai_rows:
                lines = [f'  [{r[2]}] {r[0]} → {r[1] or "unassigned"}' for r in ai_rows]
                context_parts.append("ACTION ITEMS:\n" + "\n".join(lines))

            # 5. Cascade chains
            cursor = await db.execute(
                """SELECT cc.origin_meeting_id, cc.total_cascade_cost, cc.cascade_depth, m.title
                   FROM cascade_chains cc
                   JOIN meetings m ON cc.origin_meeting_id = m.meeting_id
                   WHERE cc.session_id = ? ORDER BY cc.total_cascade_cost DESC""",
                (session_id,),
            )
            cc_rows = await cursor.fetchall()
            if cc_rows:
                lines = [
                    f'  "{r[3]}" spawned {r[2]} follow-up meeting(s), cascade cost=${r[1]:,.0f}'
                    for r in cc_rows
                ]
                context_parts.append("CASCADE CHAINS (meetings that spawned follow-ups):\n" + "\n".join(lines))

            # 6. Anomalies
            cursor = await db.execute(
                "SELECT anomaly_type, severity, description FROM anomalies WHERE session_id = ?",
                (session_id,),
            )
            an_rows = await cursor.fetchall()
            if an_rows:
                lines = [f"  [{r[1].upper()}] {r[0]}: {r[2]}" for r in an_rows]
                context_parts.append("ANOMALIES:\n" + "\n".join(lines))

            # 7. Transcripts — include full text so the LLM can answer "what did X say"
            cursor = await db.execute(
                """SELECT t.content, m.title
                   FROM transcripts t
                   JOIN meetings m ON t.meeting_id = m.meeting_id
                   WHERE t.session_id = ?
                   ORDER BY m.start_datetime DESC""",
                (session_id,),
            )
            transcript_rows = await cursor.fetchall()
            if transcript_rows:
                blocks = []
                for content, title in transcript_rows:
                    # Trim each transcript to 2000 chars to stay within context limits
                    trimmed = content[:2000] + ("…[trimmed]" if len(content) > 2000 else "")
                    blocks.append(f"  === {title} ===\n{trimmed}")
                context_parts.append("MEETING TRANSCRIPTS (use these to answer questions about what was said or decided):\n" + "\n\n".join(blocks))

    except Exception as e:
        logger.warning(f"Context build failed: {e}")

    if not context_parts:
        return {
            "answer": "No analysis data found for this session. Please run an analysis first.",
            "relevant_meeting_ids": [],
        }

    full_context = "\n\n".join(context_parts)

    llm = get_llm(settings.INSIGHT_QUERY_MODEL, temperature=0.3)
    system_prompt = (
        "You are a meeting intelligence assistant with access to the full analysis data below. "
        "Answer the user's question precisely using numbers and quotes from the data. "
        "When asked what someone said or decided in a meeting, quote directly from the MEETING TRANSCRIPTS section. "
        "When asked about costs, sum the relevant meeting costs from the MEETINGS list. "
        "When asked about people, use the PEOPLE / FOCUS TIME section. "
        "If transcript content is available, prefer quoting it over paraphrasing. "
        "Be specific, direct, and quantitative. Only use what's in the data — never guess."
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"DATA:\n{full_context}\n\nQUESTION: {query}"),
    ]
    result = await llm.ainvoke(messages)
    return {"answer": result.content, "relevant_meeting_ids": []}


async def smart_scheduler_node(state: dict) -> dict:
    """
    Generate intelligent meeting proposal with waste prediction.
    
    TODO: Implement with LLM + historical context
    """
    return {
        "proposal": None,
        "errors": ["Scheduling feature coming soon"],
    }


def build_interaction_graph():
    """
    Build and compile the interaction graph.
    
    Handles:
    - Insight queries (Ask Meetrix)
    - Smart scheduling
    
    Returns:
        Compiled StateGraph with MemorySaver checkpointer
    """
    # For MVP, create simple pass-through graphs
    # Full implementation deferred to production
    
    builder = StateGraph(InsightState)
    builder.add_node("query", insight_query_node)
    builder.set_entry_point("query")
    builder.add_edge("query", END)
    
    graph = builder.compile(checkpointer=MemorySaver())
    
    logger.info("Interaction graph compiled")
    return graph

# Made with Bob