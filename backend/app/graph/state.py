"""
LangGraph state type definitions.
TypedDict classes for analysis pipeline and interaction graphs.
"""
from typing import TypedDict, Any
from app.models.schemas import (
    Meeting,
    MeetingClassification,
    WasteScore,
    FocusTimeScore,
    MeetingHealth,
    ActionItem,
    Anomaly,
    CascadeChain,
    NetworkGraph,
    UpcomingRisk,
    Recommendation,
    Intervention,
    ExecutiveReport,
    ROIProjection,
    ScheduleRequest,
    MeetingProposal,
)


class AnalysisState(TypedDict):
    """
    State for the 5-node analysis pipeline graph.
    Fields are populated incrementally as nodes complete.
    """
    session_id: str
    uploaded_files: dict[str, str]          # filename → content (historical_csv, upcoming_csv, transcript_N)
    config: dict[str, Any]                  # hourly_rate, cost_weight, decision_deficit_weight, …
    transcripts: dict[str, str]             # meeting_id (str) → transcript text (populated by ingest_node)
    validated_meetings: list[Meeting]       # populated by ingest_node
    meeting_classifications: list[MeetingClassification]  # populated by analyze_node
    costs: dict[str, float]                 # meeting_id (str) → dollar cost (populated by analyze_node)
    waste_scores: list[WasteScore]          # populated by analyze_node, updated by extract_node
    focus_scores: list[FocusTimeScore]      # populated by analyze_node
    meeting_health_scores: list[MeetingHealth]  # populated by analyze_node
    action_items: list[ActionItem]          # populated by extract_node (LLM call 1)
    decisions: dict[str, list[str]]         # meeting_id (str) → decisions (populated by extract_node)
    anomalies: list[Anomaly]                # populated by analyze_node
    cascade_chains: list[CascadeChain]      # populated by analyze_node
    network_graph: NetworkGraph | None      # populated by analyze_node
    upcoming_risks: list[UpcomingRisk]      # populated by ingest_node (empty if no upcoming CSV)
    recommendations: list[Recommendation]  # populated by analyze_node
    interventions: list[Intervention]       # populated by analyze_node
    executive_report: ExecutiveReport | None  # populated by synthesize_node (LLM call 2)
    roi_projection: ROIProjection | None    # populated by analyze_node
    errors: list[str]


class ScheduleState(TypedDict):
    """
    State for scheduling interaction graph.
    Single-turn request/response.
    """
    session_id: str
    request: ScheduleRequest
    proposal: MeetingProposal | None
    errors: list[str]


class InsightState(TypedDict):
    """
    State for insight query interaction graph.
    Multi-turn conversation support.
    """
    session_id: str
    query: str
    answer: str | None
    relevant_meeting_ids: list[str]
    errors: list[str]

# Made with Bob
