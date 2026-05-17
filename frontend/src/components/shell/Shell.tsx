/**
 * Kawaii-Brutalism Shell - persistent layout wrapper with processing banner.
 */

import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { useSession } from '@/contexts/SessionContext';

interface ShellProps {
  children: ReactNode;
}

export function Shell({ children }: ShellProps) {
  const { results, isProcessing, agents } = useSession();
  const meetrixScore = results?.summary_stats.meetrix_score ?? 0;

  const completedAgents = agents.filter((a) => a.status === 'complete').length;
  const totalAgents = agents.length || 5;

  return (
    <div className="flex flex-col min-h-screen">
      {/* Processing Banner */}
      {isProcessing && (
        <div className="bg-kb-lavender border-b-3 border-kb-black text-kb-black font-mono font-bold text-xs uppercase tracking-widest py-2 px-8 text-center z-50">
          ANALYSIS RUNNING — {completedAgents}/{totalAgents} AGENTS COMPLETE
        </div>
      )}

      <div className="flex flex-1 bg-kb-cream">
        <Sidebar meetrixScore={meetrixScore} />
        <main className="flex-1 px-8 py-8">
          {children}
        </main>
      </div>
    </div>
  );
}

// Made with Bob
