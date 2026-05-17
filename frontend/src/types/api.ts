/**
 * TypeScript types derived from backend Pydantic models.
 * Source: backend/app/models/schemas.py
 */

// ============================================================================
// Core Meeting Models
// ============================================================================

export interface Meeting {
  meeting_id: string;
  title: string;
  start_datetime: string;
  end_datetime: string;
  duration_minutes: number;
  attendee_emails: string[];
  organizer_email: string | null;
  is_recurring: boolean;
  recurrence_rule: string | null;
  meeting_type: string | null;
  notes_text: string | null;
}

export interface MeetingClassification {
  meeting_id: string;
  meeting_type: 'standup' | 'planning' | 'decision' | 'status-update' | 'brainstorm' | '1:1' | 'social';
  confidence: number;
}

// ============================================================================
// Analysis Results
// ============================================================================

export interface WasteScore {
  meeting_id: string;
  cost_factor: number;
  decision_deficit: number;
  participation_imbalance: number;
  recurrence_staleness: number;
  composite_score: number;
  category: 'High Waste' | 'Medium Waste' | 'Low Waste' | 'High Value';
  threshold_exceeded: boolean;
}

export interface FocusTimeScore {
  person_email: string;
  total_meeting_hours: number;
  focus_blocks_remaining: number;
  longest_focus_block_minutes: number;
  focus_percentage: number;
}

export interface MeetingHealth {
  meeting_id: string;
  has_agenda: boolean;
  duration_appropriate: boolean;
  attendee_fit_score: number;
  overall_health_score: number;
}

export interface ActionItem {
  meeting_id: string;
  description: string;
  assignee_email: string | null;
  followed_through: boolean | null;
}

export interface Anomaly {
  entity_id: string;
  entity_type: 'meeting' | 'person' | 'team';
  anomaly_type: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

export interface CascadeChain {
  origin_meeting_id: string;
  spawned_meeting_ids: string[];
  total_cascade_cost: number;
  cascade_depth: number;
}

// ============================================================================
// Network Analysis
// ============================================================================

export interface PersonNode {
  email: string;
  display_name: string;
  total_meeting_hours: number;
  centrality_score: number;
  focus_percentage: number;
  at_risk: boolean;
}

export interface MeetingEdge {
  person_a: string;
  person_b: string;
  co_occurrence_count: number;
  combined_cost: number;
}

export interface NetworkGraph {
  nodes: PersonNode[];
  edges: MeetingEdge[];
  most_central_person: string;
  highest_cost_pair: [string, string];
}

// ============================================================================
// Recommendations and Interventions
// ============================================================================

export interface Recommendation {
  meeting_id: string;
  recommended_action: 'cancel' | 'merge' | 'shorten' | 'restructure' | 'keep';
  reasoning: string;
  priority: number;
}

export interface Intervention {
  meeting_id: string;
  pre_meeting_email_template: string;
  suggested_agenda: string[];
  recommended_attendee_reduction: string[];
  alternative_format: string;
}

export interface UpcomingRisk {
  upcoming_meeting_id: string;
  title: string;
  scheduled_datetime: string;
  attendee_emails: string[];
  waste_probability: number;
  risk_factors: string[];
  recommended_intervention: string;
}

// ============================================================================
// Reports
// ============================================================================

export interface ExecutiveReport {
  period: string;
  total_cost: number;
  total_meetings: number;
  meetrix_score: number;
  summary: string;
  key_findings: string[];
  top_recommendations: string[];
  trend_direction: 'improving' | 'worsening' | 'stable';
  data_residency: string;
}

export interface ROIProjection {
  projected_annual_saving: number;
  weeks_to_break_even: number;
  top_changes: string[];
  assumptions: string[];
}

// ============================================================================
// Scheduling
// ============================================================================

export interface ScheduleRequest {
  session_id: string;
  purpose: string;
  required_decisions: string[];
  proposed_attendees: string[];
  preferred_week: string;
  duration_preference?: number;
  meeting_type_hint?: string;
}

export interface TimeSlot {
  day: string;
  start_time: string;
  end_time: string;
  attendee_overload_count: number;
  waste_probability: number;
}

export interface MeetingProposal {
  suggested_slots: TimeSlot[];
  recommended_duration: number;
  meeting_type_prediction: string;
  required_attendees: string[];
  async_update_candidates: string[];
  generated_agenda: string[];
  waste_probability: number;
  waste_risk_factors: string[];
  success_conditions: string[];
  ical_export: string;
}

// ============================================================================
// API Request/Response Models
// ============================================================================

export interface SummaryStats {
  total_meetings: number;
  total_cost: number;
  average_waste_score: number;
  high_waste_count: number;
  meetrix_score: number;
  people_in_overload: number;
  cascade_chains_count: number;
  upcoming_risks_count: number;
}

export interface AnalysisResponse {
  session_id: string;
  status: 'processing' | 'complete' | 'failed';
  error_message?: string;
  meetings?: MeetingInfo[];
  waste_scores: WasteScore[];
  meeting_classifications: MeetingClassification[];
  recommendations: Recommendation[];
  focus_scores: FocusTimeScore[];
  meeting_health_scores: MeetingHealth[];
  action_items: ActionItem[];
  anomalies: Anomaly[];
  cascade_chains: CascadeChain[];
  network_graph: NetworkGraph | null;
  upcoming_risks: UpcomingRisk[];
  interventions: Intervention[];
  executive_report: ExecutiveReport | null;
  roi_projection: ROIProjection | null;
  summary_stats: SummaryStats;
}

export interface AgentEvent {
  agent_name: string;
  tier: number;
  status: 'queued' | 'running' | 'complete' | 'failed' | 'skipped';
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface AgentStatusResponse {
  agents: AgentEvent[];
}

export interface InsightRequest {
  session_id: string;
  query: string;
}

export interface InsightResponse {
  answer: string;
  relevant_meeting_ids: string[];
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  ollama_connected: boolean;
  ollama_url: string;
  privacy_summary: {
    llm: string;
    storage: string;
    network_calls: string;
  };
}

export interface AnalyzeResponse {
  session_id: string;
}

export interface ApiError {
  detail: string;
}

export interface MeetingPreview {
  index: number;
  title: string;
  start_datetime: string;
  duration_minutes: number;
  attendee_count: number;
  is_recurring: boolean;
}

export interface MeetingInfo {
  meeting_id: string;
  title: string;
  start_datetime: string;
  duration_minutes: number;
  attendee_count: number;
  is_recurring: boolean;
  meeting_type: string | null;
}

// Made with Bob
