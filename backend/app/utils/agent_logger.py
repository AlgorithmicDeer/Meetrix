"""
Agent execution logging utility.
Writes agent status to agent_events table for AgentExecutionPanel.
"""
import logging
from datetime import datetime
from typing import Literal
import aiosqlite
from app.config import settings

logger = logging.getLogger(__name__)

AgentStatus = Literal["queued", "running", "complete", "failed", "skipped"]


async def log_agent_event(
    session_id: str,
    agent_name: str,
    tier: int,
    status: AgentStatus,
    error_message: str | None = None,
) -> None:
    """
    Log agent execution event to database.
    
    Args:
        session_id: Session identifier
        agent_name: Agent name (snake_case)
        tier: Pipeline tier number (1-6)
        status: Agent execution status
        error_message: Error message if status is "failed"
    """
    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            # Check if event already exists
            cursor = await db.execute(
                """
                SELECT id, status FROM agent_events 
                WHERE session_id = ? AND agent_name = ?
                """,
                (session_id, agent_name),
            )
            row = await cursor.fetchone()
            
            if row:
                # Update existing event
                event_id, current_status = row
                
                # Set timestamps based on status transition
                if status == "running" and current_status == "queued":
                    await db.execute(
                        """
                        UPDATE agent_events 
                        SET status = ?, started_at = ?
                        WHERE id = ?
                        """,
                        (status, datetime.utcnow(), event_id),
                    )
                elif status in ("complete", "failed", "skipped"):
                    await db.execute(
                        """
                        UPDATE agent_events 
                        SET status = ?, completed_at = ?, error_message = ?
                        WHERE id = ?
                        """,
                        (status, datetime.utcnow(), error_message, event_id),
                    )
                else:
                    await db.execute(
                        """
                        UPDATE agent_events 
                        SET status = ?, error_message = ?
                        WHERE id = ?
                        """,
                        (status, error_message, event_id),
                    )
            else:
                # Insert new event
                started_at = datetime.utcnow() if status == "running" else None
                completed_at = datetime.utcnow() if status in ("complete", "failed", "skipped") else None
                
                await db.execute(
                    """
                    INSERT INTO agent_events 
                    (session_id, agent_name, tier, status, started_at, completed_at, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (session_id, agent_name, tier, status, started_at, completed_at, error_message),
                )
            
            await db.commit()
            
    except Exception as e:
        logger.error(f"Failed to log agent event for {agent_name}: {e}")
        # Don't raise - logging failures shouldn't break the pipeline


async def initialize_agent_events(session_id: str, agent_names: list[tuple[str, int]]) -> None:
    """
    Initialize all agent events as "queued" at pipeline start.
    
    Args:
        session_id: Session identifier
        agent_names: List of (agent_name, tier) tuples
    """
    try:
        async with aiosqlite.connect(settings.DATABASE_PATH) as db:
            for agent_name, tier in agent_names:
                await db.execute(
                    """
                    INSERT INTO agent_events 
                    (session_id, agent_name, tier, status)
                    VALUES (?, ?, ?, 'queued')
                    """,
                    (session_id, agent_name, tier),
                )
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to initialize agent events: {e}")

# Made with Bob
