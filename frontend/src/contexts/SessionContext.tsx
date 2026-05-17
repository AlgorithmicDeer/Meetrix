/**
 * Session context with integrated polling for analysis state and agent status.
 */

import { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import type { AnalysisResponse, AgentEvent } from '@/types/api';
import { setSessionId as persistSessionId } from '@/lib/session';
import { getResults, getAgentStatus } from '@/lib/api';

interface SessionContextType {
  sessionId: string | null;
  results: AnalysisResponse | null;
  isProcessing: boolean;
  agents: AgentEvent[];
  setSessionId: (id: string) => void;
  setResults: (results: AnalysisResponse) => void;
  clearSession: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionIdState] = useState<string | null>(() => {
    return sessionStorage.getItem('meetrix_session_id');
  });

  const [results, setResultsState] = useState<AnalysisResponse | null>(() => {
    const stored = sessionStorage.getItem('meetrix_results');
    return stored ? (JSON.parse(stored) as AnalysisResponse) : null;
  });

  const [agents, setAgents] = useState<AgentEvent[]>([]);

  const resultsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const agentsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isProcessing = results?.status === 'processing';

  const stopPolling = useCallback(() => {
    if (resultsIntervalRef.current) {
      clearInterval(resultsIntervalRef.current);
      resultsIntervalRef.current = null;
    }
    if (agentsIntervalRef.current) {
      clearInterval(agentsIntervalRef.current);
      agentsIntervalRef.current = null;
    }
  }, []);

  const setResults = useCallback((r: AnalysisResponse) => {
    setResultsState(r);
    sessionStorage.setItem('meetrix_results', JSON.stringify(r));
  }, []);

  // Poll results every 3s
  const pollResults = useCallback(async (id: string) => {
    try {
      const data = await getResults(id);
      setResults(data);
      if (data.status === 'complete' || data.status === 'failed') {
        stopPolling();
      }
    } catch {
      // keep trying silently
    }
  }, [setResults, stopPolling]);

  // Poll agent status every 1.5s
  const pollAgents = useCallback(async (id: string) => {
    try {
      const data = await getAgentStatus(id);
      setAgents(data.agents);
    } catch {
      // keep trying silently
    }
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    // If already complete, no need to poll
    if (results?.status === 'complete' || results?.status === 'failed') {
      return;
    }

    // Kick off immediately
    pollResults(sessionId);
    pollAgents(sessionId);

    resultsIntervalRef.current = setInterval(() => pollResults(sessionId), 3000);
    agentsIntervalRef.current = setInterval(() => pollAgents(sessionId), 1500);

    return stopPolling;
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Stop agent polling once processing finishes
  useEffect(() => {
    if (results?.status === 'complete' || results?.status === 'failed') {
      stopPolling();
    }
  }, [results?.status, stopPolling]);

  const handleSetSessionId = (id: string) => {
    persistSessionId(id);
    setSessionIdState(id);
    // Reset results so polling kicks in fresh
    setResultsState(null);
    setAgents([]);
    sessionStorage.removeItem('meetrix_results');
  };

  const clearSession = () => {
    stopPolling();
    sessionStorage.removeItem('meetrix_session_id');
    sessionStorage.removeItem('meetrix_results');
    setSessionIdState(null);
    setResultsState(null);
    setAgents([]);
  };

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        results,
        isProcessing,
        agents,
        setSessionId: handleSetSessionId,
        setResults,
        clearSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

// Made with Bob
