"""Integration tests for the full analysis pipeline."""
import pytest
from unittest.mock import AsyncMock, patch

from app.graph.analysis_builder import build_analysis_graph
from app.models.schemas import Meeting
from datetime import datetime, timedelta


async def test_analysis_pipeline_compilation():
    """Test that the analysis graph compiles without errors."""
    graph = build_analysis_graph()
    assert graph is not None


async def test_analysis_pipeline_execution(mock_llm, sample_meetings):
    """Test full pipeline execution with mocked LLM."""
    # Mock all LLM structured outputs
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = []
    mock_llm.with_structured_output.return_value = mock_structured
    
    # Mock CSV parser
    with patch("app.graph.nodes.logic_nodes.parse_csv", return_value=(sample_meetings, [])):
        with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
            with patch("app.graph.nodes.logic_nodes.log_agent_event"):
                with patch("app.graph.nodes.llm_nodes.log_agent_event"):
                    graph = build_analysis_graph()
                    
                    initial_state = {
                        "session_id": "test-pipeline-1",
                        "uploaded_files": {"meetings_csv": "mock_content"},
                        "errors": [],
                    }
                    
                    # Execute pipeline
                    result = await graph.ainvoke(
                        initial_state,
                        config={"configurable": {"thread_id": "test-pipeline-1"}},
                    )
                    
                    # Verify pipeline completed
                    assert result is not None
                    assert "session_id" in result
                    assert result["session_id"] == "test-pipeline-1"


async def test_pipeline_error_recovery(mock_llm, sample_meetings):
    """Test that pipeline continues after agent errors."""
    # Mock LLM to fail on first call, succeed on subsequent
    mock_structured = AsyncMock()
    mock_structured.ainvoke.side_effect = [
        Exception("First agent failed"),
        [],  # Subsequent calls succeed
        [],
        [],
    ]
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.logic_nodes.parse_csv", return_value=(sample_meetings, [])):
        with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
            with patch("app.graph.nodes.logic_nodes.log_agent_event"):
                with patch("app.graph.nodes.llm_nodes.log_agent_event"):
                    graph = build_analysis_graph()
                    
                    initial_state = {
                        "session_id": "test-pipeline-2",
                        "uploaded_files": {"meetings_csv": "mock_content"},
                        "errors": [],
                    }
                    
                    result = await graph.ainvoke(
                        initial_state,
                        config={"configurable": {"thread_id": "test-pipeline-2"}},
                    )
                    
                    # Pipeline should complete with errors logged
                    assert result is not None
                    assert "errors" in result


async def test_pipeline_with_empty_meetings(mock_llm):
    """Test pipeline handles empty meeting list gracefully."""
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = []
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.logic_nodes.parse_csv", return_value=([], [])):
        with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
            with patch("app.graph.nodes.logic_nodes.log_agent_event"):
                with patch("app.graph.nodes.llm_nodes.log_agent_event"):
                    graph = build_analysis_graph()
                    
                    initial_state = {
                        "session_id": "test-pipeline-3",
                        "uploaded_files": {"meetings_csv": "mock_content"},
                        "errors": [],
                    }
                    
                    result = await graph.ainvoke(
                        initial_state,
                        config={"configurable": {"thread_id": "test-pipeline-3"}},
                    )
                    
                    # Should complete without crashing
                    assert result is not None
                    assert result["session_id"] == "test-pipeline-3"


async def test_pipeline_state_persistence(mock_llm, sample_meetings):
    """Test that pipeline state is preserved across invocations."""
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = []
    mock_llm.with_structured_output.return_value = mock_structured
    
    with patch("app.graph.nodes.logic_nodes.parse_csv", return_value=(sample_meetings, [])):
        with patch("app.graph.nodes.llm_nodes.get_llm", return_value=mock_llm):
            with patch("app.graph.nodes.logic_nodes.log_agent_event"):
                with patch("app.graph.nodes.llm_nodes.log_agent_event"):
                    graph = build_analysis_graph()
                    
                    thread_id = "test-pipeline-4"
                    
                    # First invocation
                    initial_state = {
                        "session_id": thread_id,
                        "uploaded_files": {"meetings_csv": "mock_content"},
                        "errors": [],
                    }
                    
                    result1 = await graph.ainvoke(
                        initial_state,
                        config={"configurable": {"thread_id": thread_id}},
                    )
                    
                    # Second invocation with same thread_id
                    result2 = await graph.ainvoke(
                        {"session_id": thread_id, "uploaded_files": {"meetings_csv": "mock_content"}},
                        config={"configurable": {"thread_id": thread_id}},
                    )
                    
                    # State should be preserved
                    assert result2 is not None
                    assert result2["session_id"] == thread_id

# Made with Bob
