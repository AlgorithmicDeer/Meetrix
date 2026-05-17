"""Tests for LLM-based agents using mocked LLM responses."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.graph.nodes.llm_nodes import (
    meeting_type_classifier_agent,
    decision_extraction_agent,
    meeting_health_agent,
    action_item_tracker_agent,
    root_cause_agent,
    recommendation_agent,
    intervention_engine_agent,
    report_generation_agent,
    upcoming_risk_agent,
)
from app.models.schemas import MeetingClassification, MeetingHealth


async def test_meeting_type_classifier_agent(mock_llm, sample_meetings):
    """Test meeting type classification with mocked LLM."""
    state = {
        "session_id": "test-1",
        "validated_meetings": sample_meetings,
        "errors": [],
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = [
        {
            "meeting_id": str(sample_meetings[0].meeting_id),
            "meeting_type": "standup",
            "confidence": 0.95
        },
        {
            "meeting_id": str(sample_meetings[1].meeting_id),
            "meeting_type": "planning",
            "confidence": 0.88
        },
        {
            "meeting_id": str(sample_meetings[2].meeting_id),
            "meeting_type": "status-update",
            "confidence": 0.92
        },
    ]
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await meeting_type_classifier_agent(state)
    
    assert "meeting_classifications" in result
    assert len(result["meeting_classifications"]) == 3
    assert all(0.0 <= mt.confidence <= 1.0 for mt in result["meeting_classifications"])


async def test_decision_extraction_agent(mock_llm, sample_meetings):
    """Test decision extraction with mocked LLM."""
    state = {
        "session_id": "test-2",
        "validated_meetings": sample_meetings,
        "errors": [],
        "parallel_analysis": {},
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = [
        {
            "meeting_id": str(sample_meetings[1].meeting_id),
            "decisions": ["Launch new feature in Q2", "Approved budget increase"]
        },
    ]
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await decision_extraction_agent(state)
    
    assert "parallel_analysis" in result
    assert "decisions" in result["parallel_analysis"]


async def test_meeting_health_agent(mock_llm, sample_meetings):
    """Test meeting health assessment with mocked LLM."""
    state = {
        "session_id": "test-3",
        "validated_meetings": sample_meetings,
        "meeting_classifications": [],
        "errors": [],
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = [
        {
            "meeting_id": str(sample_meetings[0].meeting_id),
            "has_agenda": True,
            "duration_appropriate": True,
            "attendee_fit_score": 0.9,
            "overall_health_score": 0.85,
        },
    ]
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await meeting_health_agent(state)
    
    assert "meeting_health_scores" in result
    assert all(0.0 <= h.overall_health_score <= 1.0 for h in result["meeting_health_scores"])


async def test_action_item_tracker_agent(mock_llm, sample_meetings):
    """Test action item tracking with mocked LLM."""
    state = {
        "session_id": "test-4",
        "validated_meetings": sample_meetings,
        "errors": [],
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = [
        {
            "meeting_id": str(sample_meetings[1].meeting_id),
            "description": "Finalize feature spec",
            "assignee_email": "alice@example.com"
        }
    ]
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await action_item_tracker_agent(state)
    
    assert "action_items" in result


async def test_root_cause_agent(mock_llm, sample_meetings, sample_waste_scores):
    """Test root cause analysis with mocked LLM."""
    state = {
        "session_id": "test-5",
        "validated_meetings": sample_meetings,
        "waste_scores": sample_waste_scores,
        "meeting_classifications": [],
        "errors": [],
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = {
        "narrative": "This meeting scored high on waste due to lack of documented decisions and high participation imbalance."
    }
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await root_cause_agent(state)
    
    assert "root_causes" in result


async def test_recommendation_agent(mock_llm, sample_meetings, sample_waste_scores):
    """Test recommendation generation with mocked LLM."""
    state = {
        "session_id": "test-6",
        "validated_meetings": sample_meetings,
        "waste_scores": sample_waste_scores,
        "meeting_classifications": [],
        "root_causes": {},
        "errors": [],
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = {
        "recommended_action": "cancel",
        "reasoning": "No decisions made in 8 weeks",
        "priority": 1
    }
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await recommendation_agent(state)
    
    assert "recommendations" in result


async def test_intervention_engine_agent(mock_llm, sample_meetings, sample_waste_scores):
    """Test intervention generation with mocked LLM."""
    state = {
        "session_id": "test-7",
        "validated_meetings": sample_meetings,
        "waste_scores": sample_waste_scores,
        "root_causes": {},
        "errors": [],
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = {
        "pre_meeting_email_template": "Subject: Restructuring meeting...",
        "suggested_agenda": ["Item 1", "Item 2"],
        "recommended_attendee_reduction": ["eve@example.com"],
        "alternative_format": "Replace with async updates"
    }
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await intervention_engine_agent(state)
    
    assert "interventions" in result


async def test_report_generation_agent(mock_llm, sample_meetings, sample_waste_scores):
    """Test executive report generation with mocked LLM."""
    state = {
        "session_id": "test-8",
        "validated_meetings": sample_meetings,
        "waste_scores": sample_waste_scores,
        "recommendations": [],
        "focus_scores": [],
        "meeting_health_scores": [],
        "cascade_chains": [],
        "roi_projection": None,
        "parallel_analysis": {"cost": {}},
        "errors": [],
    }
    
    # Mock structured output
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = {
        "summary": "Test summary of meeting analysis",
        "key_findings": ["Finding 1", "Finding 2", "Finding 3", "Finding 4", "Finding 5"],
        "top_recommendations": ["Rec 1", "Rec 2", "Rec 3", "Rec 4", "Rec 5"],
    }
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await report_generation_agent(state)
    
    assert "executive_report" in result


async def test_upcoming_risk_agent(mock_llm, sample_meetings):
    """Test upcoming meeting risk assessment with mocked LLM."""
    state = {
        "session_id": "test-9",
        "validated_meetings": sample_meetings,
        "uploaded_files": {"upcoming_csv": "mock_csv_content"},
        "focus_scores": [],
        "waste_scores": [],
        "errors": [],
    }
    
    # Mock CSV parser
    with patch("app.utils.csv_parser.parse_csv", return_value=([], [])):
        with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
            with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
                result = await upcoming_risk_agent(state)
    
    assert "upcoming_risks" in result


async def test_llm_agent_error_handling(mock_llm, sample_meetings):
    """Test that LLM agents handle errors gracefully."""
    state = {
        "session_id": "test-10",
        "validated_meetings": sample_meetings,
        "errors": [],
    }
    
    # Mock LLM to raise an exception
    mock_structured = AsyncMock()
    mock_structured.ainvoke.side_effect = Exception("LLM connection failed")
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
        with patch("app.graph.nodes.llm_nodes.log_agent_event", new_callable=AsyncMock):
            result = await meeting_type_classifier_agent(state)
    
    # Should return empty classifications instead of crashing
    assert "meeting_classifications" in result
    assert result["meeting_classifications"] == []

# Made with Bob
