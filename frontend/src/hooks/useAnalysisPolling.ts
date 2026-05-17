/**
 * Custom hook for polling analysis results.
 * Polls /api/v1/results/:id every 3 seconds until status is complete or failed.
 */

import { useState, useEffect, useCallback } from 'react';
import { getResults } from '@/lib/api';
import type { AnalysisResponse } from '@/types/api';

export function useAnalysisPolling(sessionId: string | null) {
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const poll = useCallback(async () => {
    if (!sessionId) return;

    try {
      setIsLoading(true);
      setError(null);
      const data = await getResults(sessionId);
      setResults(data);

      // Stop polling if complete or failed
      if (data.status === 'complete' || data.status === 'failed') {
        return true; // Signal to stop polling
      }
      return false;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch results');
      return true; // Stop polling on error
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;

    // Initial poll
    poll();

    // Set up interval
    const interval = setInterval(async () => {
      const shouldStop = await poll();
      if (shouldStop) {
        clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [sessionId, poll]);

  return { results, isLoading, error };
}

// Made with Bob
