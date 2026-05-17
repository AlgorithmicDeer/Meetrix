/**
 * Custom hook for polling agent execution status.
 * Polls /api/v1/sessions/:id/agent-status every 1 second while processing.
 */

import { useState, useEffect, useCallback } from 'react';
import { getAgentStatus } from '@/lib/api';
import type { AgentEvent } from '@/types/api';

export function useAgentStatus(sessionId: string | null, isProcessing: boolean) {
  const [agents, setAgents] = useState<AgentEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const poll = useCallback(async () => {
    if (!sessionId || !isProcessing) return;

    try {
      setError(null);
      const data = await getAgentStatus(sessionId);
      setAgents(data.agents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent status');
    }
  }, [sessionId, isProcessing]);

  useEffect(() => {
    if (!sessionId || !isProcessing) return;

    // Initial poll
    poll();

    // Set up interval
    const interval = setInterval(poll, 1000);

    return () => clearInterval(interval);
  }, [sessionId, isProcessing, poll]);

  return { agents, error };
}

// Made with Bob
