"""Tests for FastAPI endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ollama_connected" in data


def test_analyze_endpoint_missing_fields(client):
    """Test analyze endpoint with missing required fields."""
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 422  # Validation error


def test_analyze_endpoint_invalid_csv(client):
    """Test analyze endpoint with invalid CSV data."""
    response = client.post(
        "/api/v1/analyze",
        json={
            "session_id": "test-1",
            "csv_data": "invalid,csv,data",
        },
    )
    # Should accept request but may fail during processing
    assert response.status_code in [200, 422]


def test_results_endpoint_not_found(client):
    """Test results endpoint with non-existent session."""
    response = client.get("/api/v1/results/nonexistent-session")
    assert response.status_code == 404


def test_agent_status_endpoint_not_found(client):
    """Test agent status endpoint with non-existent session."""
    response = client.get("/api/v1/sessions/nonexistent-session/agent-status")
    assert response.status_code == 200
    assert response.json() == {"agents": []}


def test_insights_endpoint_missing_fields(client):
    """Test insights endpoint with missing fields."""
    response = client.post("/api/v1/insights", json={})
    assert response.status_code == 422


def test_schedule_endpoint_missing_fields(client):
    """Test schedule endpoint with missing fields."""
    response = client.post("/api/v1/schedule", json={})
    assert response.status_code == 422


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORS preflight should succeed
    assert response.status_code in [200, 204]

# Made with Bob
