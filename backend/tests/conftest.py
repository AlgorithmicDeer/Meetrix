"""Shared pytest fixtures for Meetrix tests."""
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import aiosqlite
from langchain_core.messages import AIMessage

from app.models.schemas import (
    Meeting,
    MeetingClassification,
    WasteScore,
    MeetingHealth,
    ActionItem,
    Recommendation,
    Intervention,
    FocusTimeScore,
)


@pytest.fixture
def mock_llm():
    """Mock ChatOllama that returns configurable structured output."""
    llm = MagicMock()

    # Default response for with_structured_output
    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(return_value={"result": "mock"})
    llm.with_structured_output.return_value = mock_structured

    return llm


@pytest.fixture
def sample_meetings() -> list[Meeting]:
    """Generate sample meeting data for testing."""
    base_time = datetime.now()
    
    return [
        Meeting(
            meeting_id=uuid4(),
            title="Daily Standup",
            start_datetime=base_time,
            end_datetime=base_time + timedelta(minutes=15),
            duration_minutes=15,
            attendee_emails=["alice@example.com", "bob@example.com", "carol@example.com"],
            organizer_email="alice@example.com",
            is_recurring=True,
            recurrence_rule="FREQ=DAILY",
            notes_text=None,
        ),
        Meeting(
            meeting_id=uuid4(),
            title="Product Planning",
            start_datetime=base_time + timedelta(hours=2),
            end_datetime=base_time + timedelta(hours=3),
            duration_minutes=60,
            attendee_emails=["bob@example.com", "alice@example.com", "david@example.com", "eve@example.com"],
            organizer_email="bob@example.com",
            is_recurring=False,
            recurrence_rule=None,
            notes_text="Discussed Q2 roadmap. Decision: Launch feature X in May.",
        ),
        Meeting(
            meeting_id=uuid4(),
            title="Status Update",
            start_datetime=base_time + timedelta(hours=4),
            end_datetime=base_time + timedelta(hours=4, minutes=30),
            duration_minutes=30,
            attendee_emails=["carol@example.com", "alice@example.com", "bob@example.com", "david@example.com", "eve@example.com"],
            organizer_email="carol@example.com",
            is_recurring=True,
            recurrence_rule="FREQ=WEEKLY",
            notes_text="Team updates shared. No decisions made.",
        ),
    ]


@pytest.fixture
def sample_meeting_classifications(sample_meetings) -> list[MeetingClassification]:
    """Sample meeting type classifications."""
    return [
        MeetingClassification(
            meeting_id=sample_meetings[0].meeting_id,
            meeting_type="standup",
            confidence=0.95
        ),
        MeetingClassification(
            meeting_id=sample_meetings[1].meeting_id,
            meeting_type="planning",
            confidence=0.88
        ),
        MeetingClassification(
            meeting_id=sample_meetings[2].meeting_id,
            meeting_type="status-update",
            confidence=0.92
        ),
    ]


@pytest.fixture
def sample_waste_scores(sample_meetings) -> list[WasteScore]:
    """Sample waste score data."""
    return [
        WasteScore(
            meeting_id=sample_meetings[0].meeting_id,
            cost_factor=0.15,
            decision_deficit=0.20,
            participation_imbalance=0.10,
            recurrence_staleness=0.25,
            composite_score=0.18,
            category="High Value",
            threshold_exceeded=False,
        ),
        WasteScore(
            meeting_id=sample_meetings[1].meeting_id,
            cost_factor=0.35,
            decision_deficit=0.20,
            participation_imbalance=0.30,
            recurrence_staleness=0.00,
            composite_score=0.28,
            category="Low Waste",
            threshold_exceeded=False,
        ),
        WasteScore(
            meeting_id=sample_meetings[2].meeting_id,
            cost_factor=0.60,
            decision_deficit=0.90,
            participation_imbalance=0.70,
            recurrence_staleness=0.85,
            composite_score=0.76,
            category="High Waste",
            threshold_exceeded=True,
        ),
    ]


@pytest.fixture
def sample_health_scores(sample_meetings) -> list[MeetingHealth]:
    """Sample meeting health data."""
    return [
        MeetingHealth(
            meeting_id=sample_meetings[0].meeting_id,
            has_agenda=True,
            duration_appropriate=True,
            attendee_fit_score=0.9,
            overall_health_score=0.85,
        ),
        MeetingHealth(
            meeting_id=sample_meetings[1].meeting_id,
            has_agenda=True,
            duration_appropriate=True,
            attendee_fit_score=0.7,
            overall_health_score=0.75,
        ),
        MeetingHealth(
            meeting_id=sample_meetings[2].meeting_id,
            has_agenda=False,
            duration_appropriate=False,
            attendee_fit_score=0.3,
            overall_health_score=0.4,
        ),
    ]


@pytest.fixture
def sample_action_items(sample_meetings) -> list[ActionItem]:
    """Sample action item data."""
    return [
        ActionItem(
            meeting_id=sample_meetings[1].meeting_id,
            description="Finalize feature spec by next Friday",
            assignee_email="alice@example.com",
            followed_through=None,
        ),
    ]


@pytest.fixture
def sample_recommendations(sample_meetings) -> list[Recommendation]:
    """Sample recommendation data."""
    return [
        Recommendation(
            meeting_id=sample_meetings[2].meeting_id,
            recommended_action="cancel",
            reasoning="Status updates can be shared asynchronously via Slack. No decisions made in 8 weeks.",
            priority=1,
        ),
    ]


@pytest.fixture
def sample_interventions(sample_meetings) -> list[Intervention]:
    """Sample intervention data."""
    return [
        Intervention(
            meeting_id=sample_meetings[2].meeting_id,
            pre_meeting_email_template="Subject: Restructuring Weekly Status Update\n\nTeam,\n\nTo improve efficiency...",
            suggested_agenda=["Quick wins from last week", "Blockers requiring group discussion", "Next week priorities"],
            recommended_attendee_reduction=["eve@example.com"],
            alternative_format="Replace weekly 30min meeting with async Slack updates + monthly 15min sync",
        ),
    ]


@pytest.fixture
def sample_focus_scores() -> list[FocusTimeScore]:
    """Sample focus time analysis data."""
    return [
        FocusTimeScore(
            person_email="alice@example.com",
            total_meeting_hours=25.5,
            focus_blocks_remaining=3,
            longest_focus_block_minutes=90,
            focus_percentage=0.36,
        ),
        FocusTimeScore(
            person_email="bob@example.com",
            total_meeting_hours=18.0,
            focus_blocks_remaining=5,
            longest_focus_block_minutes=120,
            focus_percentage=0.55,
        ),
        FocusTimeScore(
            person_email="carol@example.com",
            total_meeting_hours=32.0,
            focus_blocks_remaining=1,
            longest_focus_block_minutes=45,
            focus_percentage=0.20,
        ),
    ]


@pytest.fixture
async def test_db() -> AsyncGenerator[str, None]:
    """Create a temporary test database."""
    db_path = ":memory:"
    
    async with aiosqlite.connect(db_path) as db:
        # Create minimal schema for testing
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                tier INTEGER NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
            )
        """)
        
        await db.commit()
    
    yield db_path

# Made with Bob
