"""
Pydantic models for all data structures.
Shared between LangGraph state and FastAPI response schemas.
"""
from datetime import datetime, date, time
from typing import Literal, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Core Meeting Models
# ============================================================================

class Meeting(BaseModel):
    """Meeting data from CSV upload."""
    meeting_id: UUID
    title: str
    start_datetime: datetime
    end_datetime: datetime
    duration_minutes: int
    attendee_emails: list[EmailStr]
    organizer_email: EmailStr | None = None
    is_recurring: bool = False
    recurrence_rule: str | None = None
    meeting_type: str | None = None
    notes_text: str | None = None


class MeetingClassification(BaseModel):
    """Meeting type classification result."""
    meeting_id: UUID
    meeting_type: Literal["standup", "planning", "decision", "status-update", "brainstorm", "1:1", "social"]
    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================================
# Analysis Results
# ============================================================================

class WasteScore(BaseModel):
    """Composite waste score for a meeting."""
    meeting_id: UUID
    cost_factor: float = Field(ge=0.0, le=1.0)
    decision_deficit: float = Field(ge=0.0, le=1.0)
    participation_imbalance: float = Field(ge=0.0, le=1.0)
    recurrence_staleness: float = Field(ge=0.0, le=1.0)
    composite_score: float = Field(ge=0.0, le=1.0)
    category: Literal["High Waste", "Medium Waste", "Low Waste", "High Value"]
    threshold_exceeded: bool


class FocusTimeScore(BaseModel):
    """Focus time analysis per person."""
    person_email: str
    total_meeting_hours: float
    focus_blocks_remaining: int
    longest_focus_block_minutes: int
    focus_percentage: float = Field(ge=0.0, le=1.0)


class MeetingHealth(BaseModel):
    """Meeting hygiene score."""
    meeting_id: UUID
    has_agenda: bool
    duration_appropriate: bool
    attendee_fit_score: float = Field(ge=0.0, le=1.0)
    overall_health_score: float = Field(ge=0.0, le=1.0)


class ActionItem(BaseModel):
    """Extracted action item from meeting notes."""
    meeting_id: UUID
    description: str
    assignee_email: str | None = None
    followed_through: bool | None = None


class Anomaly(BaseModel):
    """Detected anomaly in meeting patterns."""
    entity_id: str
    entity_type: Literal["meeting", "person", "team"]
    anomaly_type: str
    severity: Literal["low", "medium", "high"]
    description: str


class CascadeChain(BaseModel):
    """Cascade chain of follow-up meetings."""
    origin_meeting_id: UUID
    spawned_meeting_ids: list[UUID]
    total_cascade_cost: float
    cascade_depth: int


# ============================================================================
# Network Analysis
# ============================================================================

class PersonNode(BaseModel):
    """Person node in meeting network."""
    email: str
    display_name: str
    total_meeting_hours: float
    centrality_score: float = Field(ge=0.0, le=1.0)
    focus_percentage: float = Field(ge=0.0, le=1.0)
    at_risk: bool


class MeetingEdge(BaseModel):
    """Edge between two people in meeting network."""
    person_a: str
    person_b: str
    co_occurrence_count: int
    combined_cost: float


class NetworkGraph(BaseModel):
    """Complete meeting network graph."""
    nodes: list[PersonNode]
    edges: list[MeetingEdge]
    most_central_person: str
    highest_cost_pair: tuple[str, str]


# ============================================================================
# Recommendations and Interventions
# ============================================================================

class Recommendation(BaseModel):
    """Recommended action for a meeting."""
    meeting_id: UUID
    recommended_action: Literal["cancel", "merge", "shorten", "restructure", "keep"]
    reasoning: str
    priority: int = Field(ge=1, le=5)


class Intervention(BaseModel):
    """Ready-to-use intervention materials."""
    meeting_id: UUID
    pre_meeting_email_template: str
    suggested_agenda: list[str]
    recommended_attendee_reduction: list[EmailStr]
    alternative_format: str


class UpcomingRisk(BaseModel):
    """Risk assessment for upcoming meeting."""
    upcoming_meeting_id: UUID
    title: str
    scheduled_datetime: datetime
    attendee_emails: list[EmailStr]
    waste_probability: float = Field(ge=0.0, le=1.0)
    risk_factors: list[str]
    recommended_intervention: str


# ============================================================================
# Reports
# ============================================================================

class ExecutiveReport(BaseModel):
    """Executive summary report."""
    period: str
    total_cost: float
    total_meetings: int
    meetrix_score: int = Field(ge=0, le=100)
    summary: str
    key_findings: list[str]
    top_recommendations: list[str]
    trend_direction: Literal["improving", "worsening", "stable"]
    data_residency: str = "All data processed and stored locally. No external API calls."


class ROIProjection(BaseModel):
    """ROI projection from implementing recommendations."""
    projected_annual_saving: float
    weeks_to_break_even: int
    top_changes: list[str]
    assumptions: list[str]


# ============================================================================
# Scheduling
# ============================================================================

class ScheduleRequest(BaseModel):
    """Request for smart meeting scheduling."""
    session_id: str
    purpose: str
    required_decisions: list[str]
    proposed_attendees: list[EmailStr]
    preferred_week: date
    duration_preference: int | None = None
    meeting_type_hint: str | None = None


class TimeSlot(BaseModel):
    """Proposed time slot for meeting."""
    day: date
    start_time: time
    end_time: time
    attendee_overload_count: int
    waste_probability: float = Field(ge=0.0, le=1.0)


class MeetingProposal(BaseModel):
    """Complete meeting proposal with risk assessment."""
    suggested_slots: list[TimeSlot]
    recommended_duration: int
    meeting_type_prediction: str
    required_attendees: list[EmailStr]
    async_update_candidates: list[EmailStr]
    generated_agenda: list[str]
    waste_probability: float = Field(ge=0.0, le=1.0)
    waste_risk_factors: list[str]
    success_conditions: list[str]
    ical_export: str


# ============================================================================
# API Request/Response Models
# ============================================================================

class MeetingInfo(BaseModel):
    """Lightweight meeting info included in AnalysisResponse for the Meetings page."""
    meeting_id: str
    title: str
    start_datetime: str
    duration_minutes: int
    attendee_count: int
    is_recurring: bool
    meeting_type: str | None = None


class SummaryStats(BaseModel):
    """Summary statistics for dashboard."""
    total_meetings: int
    total_cost: float
    average_waste_score: float
    high_waste_count: int
    meetrix_score: int = Field(ge=0, le=100)
    people_in_overload: int
    cascade_chains_count: int
    upcoming_risks_count: int


class AnalysisResponse(BaseModel):
    """Complete analysis results."""
    session_id: str
    status: Literal["processing", "complete", "failed"]
    error_message: str | None = None
    meetings: list[MeetingInfo] = []
    waste_scores: list[WasteScore] = []
    meeting_classifications: list[MeetingClassification] = []
    recommendations: list[Recommendation] = []
    focus_scores: list[FocusTimeScore] = []
    meeting_health_scores: list[MeetingHealth] = []
    action_items: list[ActionItem] = []
    anomalies: list[Anomaly] = []
    cascade_chains: list[CascadeChain] = []
    network_graph: NetworkGraph | None = None
    upcoming_risks: list[UpcomingRisk] = []
    interventions: list[Intervention] = []
    executive_report: ExecutiveReport | None = None
    roi_projection: ROIProjection | None = None
    summary_stats: SummaryStats


class AgentEvent(BaseModel):
    """Agent execution status event."""
    agent_name: str
    tier: int
    status: Literal["queued", "running", "complete", "failed", "skipped"]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class InsightRequest(BaseModel):
    """Natural language query request."""
    session_id: str
    query: str = Field(min_length=1)


class InsightResponse(BaseModel):
    """Natural language query response."""
    answer: str
    relevant_meeting_ids: list[str] = []


# ============================================================================
# Transcript upload models
# ============================================================================

class MeetingPreview(BaseModel):
    """Lightweight meeting info for preview before analysis."""
    index: int              # position in CSV (0-based)
    title: str
    start_datetime: datetime
    duration_minutes: int
    attendee_count: int
    is_recurring: bool


class TranscriptUpload(BaseModel):
    """Transcript associated with a meeting by its CSV index."""
    meeting_index: int      # matches MeetingPreview.index
    filename: str
    content: str            # text content of the transcript

# Made with Bob
