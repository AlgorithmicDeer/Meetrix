"""Tests for deterministic logic agents (no LLM calls)."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.graph.nodes.logic_nodes import (
    data_validation_agent,
    cost_analysis_agent,
    participation_analysis_agent,
    recurrence_analysis_agent,
    focus_time_agent,
    waste_synthesis_agent,
    anomaly_detection_agent,
    network_analysis_agent,
    compute_roi_projection,
)
from app.models.schemas import Meeting


async def test_data_validation_agent_valid_data(sample_meetings):
    """Test data validation with valid meeting data."""
    state = {
        "session_id": "test-1",
        "uploaded_files": {"historical_csv": "mock_content"},
        "errors": [],
    }
    
    # Mock CSV parser to return sample meetings
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.parse_csv", return_value=(sample_meetings, [])):
        with patch("app.graph.nodes.logic_nodes.log_agent_event"):
            result = await data_validation_agent(state)
    
    assert "validated_meetings" in result
    assert len(result["validated_meetings"]) == len(sample_meetings)


async def test_data_validation_agent_invalid_data():
    """Test data validation with invalid meeting data."""
    invalid_meeting = Meeting(
        meeting_id=uuid4(),
        title="",  # Empty title
        start_datetime=datetime.now(),
        end_datetime=datetime.now() - timedelta(hours=1),  # End before start
        duration_minutes=-30,  # Negative duration
        attendee_emails=[],  # No attendees
        organizer_email=None,
        is_recurring=False,
        recurrence_rule=None,
        notes_text=None,
    )
    
    state = {
        "session_id": "test-2",
        "uploaded_files": {"meetings_csv": "mock_content"},
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.parse_csv", return_value=([invalid_meeting], [])):
        with patch("app.graph.nodes.logic_nodes.log_agent_event"):
            result = await data_validation_agent(state)
    
    # Should filter out invalid meetings
    assert "validated_meetings" in result


async def test_cost_analysis_agent(sample_meetings):
    """Test cost analysis calculation."""
    state = {
        "session_id": "test-3",
        "validated_meetings": sample_meetings,
        "parallel_analysis": {},
        "config": {},
        "errors": [],
    }

    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await cost_analysis_agent(state)
    
    assert "parallel_analysis" in result
    assert "cost" in result["parallel_analysis"]


async def test_participation_analysis_agent(sample_meetings):
    """Test participation analysis."""
    state = {
        "session_id": "test-4",
        "validated_meetings": sample_meetings,
        "parallel_analysis": {},
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await participation_analysis_agent(state)
    
    assert "parallel_analysis" in result
    assert "participation" in result["parallel_analysis"]


async def test_recurrence_analysis_agent(sample_meetings):
    """Test recurrence pattern analysis."""
    state = {
        "session_id": "test-5",
        "validated_meetings": sample_meetings,
        "parallel_analysis": {},
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await recurrence_analysis_agent(state)
    
    assert "parallel_analysis" in result
    assert "recurrence" in result["parallel_analysis"]


async def test_focus_time_agent(sample_meetings):
    """Test focus time calculation."""
    state = {
        "session_id": "test-6",
        "validated_meetings": sample_meetings,
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await focus_time_agent(state)
    
    assert "focus_scores" in result
    assert isinstance(result["focus_scores"], list)


async def test_waste_synthesis_agent(sample_meetings, sample_waste_scores):
    """Test waste synthesis aggregation."""
    state = {
        "session_id": "test-8",
        "validated_meetings": sample_meetings,
        "meeting_classifications": [],
        "parallel_analysis": {
            "cost": {},
            "decisions": {},
            "participation": {},
            "recurrence": {},
        },
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await waste_synthesis_agent(state)
    
    assert "waste_scores" in result
    assert isinstance(result["waste_scores"], list)


async def test_anomaly_detection_agent(sample_meetings, sample_waste_scores):
    """Test anomaly detection."""
    state = {
        "session_id": "test-9",
        "validated_meetings": sample_meetings,
        "waste_scores": sample_waste_scores,
        "focus_scores": [],
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await anomaly_detection_agent(state)
    
    assert "anomalies" in result
    assert isinstance(result["anomalies"], list)


async def test_network_analysis_agent(sample_meetings):
    """Test network analysis."""
    state = {
        "session_id": "test-10",
        "validated_meetings": sample_meetings,
        "focus_scores": [],
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await network_analysis_agent(state)
    
    assert "network_graph" in result


async def test_cascade_detection_agent(sample_meetings):
    """Test cascade chain detection."""
    state = {
        "session_id": "test-11",
        "validated_meetings": sample_meetings,
        "parallel_analysis": {"cost": {}},
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await anomaly_detection_agent(state)
    
    assert "cascade_chains" in result
    assert isinstance(result["cascade_chains"], list)


async def test_roi_projection_agent(sample_meetings, sample_recommendations):
    """Test ROI projection calculation."""
    state = {
        "session_id": "test-12",
        "validated_meetings": sample_meetings,
        "recommendations": sample_recommendations,
        "waste_scores": [],
        "parallel_analysis": {"cost": {}},
        "errors": [],
    }
    
    from unittest.mock import patch
    with patch("app.graph.nodes.logic_nodes.log_agent_event"):
        result = await compute_roi_projection(state)
    
    assert "roi_projection" in result

# Made with Bob
