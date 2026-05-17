/**
 * Typed API client for Meetrix backend.
 * All fetch calls go through this file - never fetch directly in components.
 */

import type {
  AnalysisResponse,
  AgentStatusResponse,
  InsightRequest,
  InsightResponse,
  ScheduleRequest,
  MeetingProposal,
  HealthResponse,
  AnalyzeResponse,
  MeetingPreview,
} from '@/types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail ?? 'Request failed');
  }

  return response.json() as Promise<T>;
}

/**
 * Parse CSV and return a preview of meetings without triggering analysis.
 */
export async function parsePreview(historicalCsv: File): Promise<MeetingPreview[]> {
  const formData = new FormData();
  formData.append('historical_csv', historicalCsv);

  const response = await fetch(`${BASE_URL}/api/v1/parse-preview`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail ?? 'Preview failed');
  }

  return response.json() as Promise<MeetingPreview[]>;
}

/**
 * Upload calendar data and trigger analysis pipeline.
 * Returns session_id immediately, pipeline runs in background.
 */
export async function analyze(
  historicalCsv: File,
  upcomingCsv: File | null,
  config: {
    hourly_rate: number;
    cost_weight: number;
    decision_deficit_weight: number;
    participation_weight: number;
    recurrence_weight: number;
  },
  transcripts?: Record<number, string>
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('historical_csv', historicalCsv);
  if (upcomingCsv) {
    formData.append('upcoming_csv', upcomingCsv);
  }
  formData.append('config', JSON.stringify(config));
  if (transcripts && Object.keys(transcripts).length > 0) {
    formData.append('transcripts_json', JSON.stringify(transcripts));
  }

  const response = await fetch(`${BASE_URL}/api/v1/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail ?? 'Analysis upload failed');
  }

  return response.json() as Promise<AnalyzeResponse>;
}

/**
 * Retrieve analysis results for a session.
 * Frontend polls this endpoint every 3 seconds.
 */
export async function getResults(sessionId: string): Promise<AnalysisResponse> {
  return request<AnalysisResponse>(`/api/v1/results/${sessionId}`);
}

/**
 * Retrieve live agent execution status.
 * Frontend polls this every 1 second during analysis.
 */
export async function getAgentStatus(sessionId: string): Promise<AgentStatusResponse> {
  return request<AgentStatusResponse>(`/api/v1/sessions/${sessionId}/agent-status`);
}

/**
 * Ask natural language questions about stored analysis results.
 */
export async function queryInsights(req: InsightRequest): Promise<InsightResponse> {
  return request<InsightResponse>('/api/v1/insights', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/**
 * Generate intelligent meeting proposal with waste prediction.
 */
export async function scheduleMeeting(req: ScheduleRequest): Promise<MeetingProposal> {
  return request<MeetingProposal>('/api/v1/schedule', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

/**
 * Check service health and Ollama connectivity.
 */
export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/v1/health');
}

// Made with Bob
