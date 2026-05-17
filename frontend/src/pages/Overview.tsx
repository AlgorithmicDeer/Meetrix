/**
 * Overview Page - AgentExecutionPanel while processing, full dashboard when complete.
 */

import { Navigate, Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';
import { InfoTooltip } from '@/components/ui/InfoTooltip';

const AGENT_NAMES: Record<string, string> = {
  ingest_agent: '📥 Ingest & Validate',
  analyze_agent: '🔬 Analyze',
  extract_agent: '🎯 Extract Insights',
  synthesize_agent: '📝 Synthesize Report',
  save_agent: '💾 Save Results',
};

const TIER_LABELS: Record<number, string> = {
  1: 'TIER 1 — INGEST',
  2: 'TIER 2 — ANALYSIS',
  3: 'TIER 3 — EXTRACTION',
  4: 'TIER 4 — SYNTHESIS',
  5: 'TIER 5 — PERSISTENCE',
};

const ACTION_COLORS: Record<string, string> = {
  cancel: 'bg-kb-coral',
  shorten: 'bg-kb-peach',
  restructure: 'bg-kb-lavender',
  keep: 'bg-kb-mint',
  merge: 'bg-kb-pink',
};

export function Overview() {
  const { sessionId, results, isProcessing, agents } = useSession();

  if (!sessionId) {
    return <Navigate to="/settings" replace />;
  }

  // Initial load: session exists but no results yet
  if (!results) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <span className="font-mono font-bold text-sm uppercase tracking-widest animate-pulse text-kb-black">
          LOADING ANALYSIS...
        </span>
        <Link
          to="/settings"
          className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50 hover:text-kb-black underline"
        >
          Back to Settings
        </Link>
      </div>
    );
  }

  // Processing state: show agent execution panel
  if (isProcessing) {
    const completedAgents = agents.filter((a) => a.status === 'complete').length;
    const totalAgents = agents.length || 5;
    const progress = Math.round((completedAgents / totalAgents) * 100);

    const agentsByTier = agents.reduce<Record<number, typeof agents>>((acc, agent) => {
      if (!acc[agent.tier]) acc[agent.tier] = [];
      acc[agent.tier].push(agent);
      return acc;
    }, {});

    const statusColors: Record<string, string> = {
      queued: 'bg-kb-muted',
      running: 'bg-kb-lavender animate-pulse',
      complete: 'bg-kb-mint',
      failed: 'bg-kb-coral',
      skipped: 'bg-kb-muted opacity-60',
    };

    return (
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-black text-3xl uppercase">OVERVIEW</h1>
        </div>

        <div className="bg-kb-white border-3 border-kb-black p-6 shadow-brutal-md">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="font-display font-black text-2xl uppercase text-kb-black">
                PIPELINE RUNNING<span className="animate-pulse">...</span>
              </h2>
              <span className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
                {completedAgents} / {totalAgents} AGENTS COMPLETE
              </span>
            </div>

            {/* Progress bar */}
            <div className="border-2 border-kb-black h-8 w-full relative overflow-hidden">
              <div
                className="h-full bg-kb-lavender transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
              <span className="absolute inset-0 flex items-center justify-center font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
                {progress}%
              </span>
            </div>

            {/* Tier breakdown */}
            <div className="space-y-4">
              {Object.entries(agentsByTier)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([tier, tierAgents]) => (
                  <div key={tier} className="border-t-2 border-kb-black pt-4">
                    <div className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50 mb-3">
                      {TIER_LABELS[Number(tier)] ?? `TIER ${tier}`}
                    </div>
                    <div className="flex flex-wrap gap-3">
                      {tierAgents.map((agent) => (
                        <div
                          key={agent.agent_name}
                          className={`${statusColors[agent.status] ?? 'bg-kb-muted'} border-2 border-kb-black px-3 py-2 shadow-brutal-sm inline-flex items-center gap-2`}
                        >
                          <span className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
                            {AGENT_NAMES[agent.agent_name] ?? agent.agent_name}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Complete state: full dashboard
  const stats = results.summary_stats;
  const recs = [...results.recommendations].sort((a, b) => a.priority - b.priority).slice(0, 5);

  const wasteAvgColor =
    stats.average_waste_score > 0.7
      ? 'bg-kb-coral'
      : stats.average_waste_score > 0.4
      ? 'bg-kb-peach'
      : 'bg-kb-mint';

  const scoreColor =
    stats.meetrix_score >= 86
      ? 'text-kb-lavender'
      : stats.meetrix_score >= 66
      ? 'text-kb-mint'
      : stats.meetrix_score >= 41
      ? 'text-kb-peach'
      : 'text-kb-coral';

  const verdict =
    stats.meetrix_score >= 86
      ? 'HEALTHY'
      : stats.meetrix_score >= 66
      ? 'NEEDS ATTENTION'
      : 'CRITICAL WASTE';

  const verdictColor =
    stats.meetrix_score >= 86
      ? 'bg-kb-mint'
      : stats.meetrix_score >= 66
      ? 'bg-kb-peach'
      : 'bg-kb-coral';

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display font-black text-3xl uppercase">OVERVIEW</h1>
        <Link
          to="/settings"
          className="border-2 border-kb-black bg-kb-white px-4 py-2 font-mono font-bold text-xs uppercase tracking-widest shadow-brutal-sm hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
        >
          ✦ New Analysis
        </Link>
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Left column (col-span-2) */}
        <div className="col-span-2 space-y-8">
          {/* 4 KPI cards in 2x2 grid */}
          <div className="grid grid-cols-2 gap-6">
            {/* Total Cost */}
            <div className="bg-kb-peach border-3 border-kb-black shadow-brutal-md p-6">
              <p className="font-mono text-xs uppercase tracking-widest mb-2 text-kb-black/60 flex items-center gap-2">
                TOTAL COST
                <InfoTooltip text="Estimated salary cost of all meeting time in the period. Calculated as: attendee hourly rate × meeting duration × number of attendees." side="top" />
              </p>
              <p className="font-display font-black text-5xl text-kb-black leading-none">
                ${stats.total_cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>

            {/* Avg Waste */}
            <div className={`${wasteAvgColor} border-3 border-kb-black shadow-brutal-md p-6`}>
              <p className="font-mono text-xs uppercase tracking-widest mb-2 text-kb-black/60 flex items-center gap-2">
                AVG WASTE
                <InfoTooltip text="Average waste score across all meetings — a composite of cost, missing decisions, unbalanced participation, and recurring meeting staleness. 0% = perfect, 100% = pure waste." side="top" />
              </p>
              <p className="font-display font-black text-5xl text-kb-black leading-none">
                {(stats.average_waste_score * 100).toFixed(0)}%
              </p>
            </div>

            {/* People Overloaded */}
            <div className="bg-kb-lavender border-3 border-kb-black shadow-brutal-md p-6">
              <p className="font-mono text-xs uppercase tracking-widest mb-2 text-kb-black/60 flex items-center gap-2">
                PEOPLE OVERLOADED
                <InfoTooltip text="Number of team members with more than 15 hours of meetings in this period (~5 hrs/week). High meeting load leaves little time for deep, focused work." side="top" />
              </p>
              <p className="font-display font-black text-5xl text-kb-black leading-none">
                {stats.people_in_overload}
              </p>
            </div>

            {/* Cascade Chains */}
            <div className="bg-kb-pink border-3 border-kb-black shadow-brutal-md p-6">
              <p className="font-mono text-xs uppercase tracking-widest mb-2 text-kb-black/60 flex items-center gap-2">
                CASCADE CHAINS
                <InfoTooltip text="Meetings that ended without decisions, causing follow-up meetings within 72 hours with the same group. These are wasteful: one meeting spawned more meetings." side="top" />
              </p>
              <p className="font-display font-black text-5xl text-kb-black leading-none">
                {stats.cascade_chains_count}
              </p>
            </div>
          </div>

          {/* Top Recommendations */}
          {recs.length > 0 && (
            <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
              <h2 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
                TOP RECOMMENDATIONS
              </h2>
              <div>
                {recs.map((rec, idx) => (
                  <div
                    key={`${rec.meeting_id}-${idx}`}
                    className="border-b-2 border-kb-black py-3 flex items-start gap-3 last:border-b-0"
                  >
                    <div className="bg-kb-lavender border-2 border-kb-black w-8 h-8 flex items-center justify-center font-mono font-black text-sm flex-shrink-0">
                      {rec.priority}
                    </div>
                    <div className="flex items-start gap-2 flex-wrap flex-1">
                      <span
                        className={`${ACTION_COLORS[rec.recommended_action] ?? 'bg-kb-muted'} border-2 border-kb-black font-mono text-xs uppercase px-2 py-1 flex-shrink-0`}
                      >
                        {rec.recommended_action}
                      </span>
                      <span className="font-sans text-sm text-kb-black">{rec.reasoning}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upcoming Risks */}
          {results.upcoming_risks.length > 0 && (
            <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
              <h2 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
                UPCOMING RISKS
              </h2>
              <div>
                {results.upcoming_risks.slice(0, 5).map((risk) => {
                  const probColor =
                    risk.waste_probability > 0.7
                      ? 'bg-kb-coral'
                      : risk.waste_probability > 0.4
                      ? 'bg-kb-peach'
                      : 'bg-kb-mint';
                  return (
                    <div
                      key={risk.upcoming_meeting_id}
                      className="border-b-2 border-kb-black py-3 last:border-b-0"
                    >
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <span className="font-mono font-bold text-sm text-kb-black truncate max-w-xs">
                          {risk.title}
                        </span>
                        <span
                          className={`${probColor} border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase`}
                        >
                          {(risk.waste_probability * 100).toFixed(0)}% WASTE RISK
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {risk.risk_factors.map((factor, i) => (
                          <span
                            key={i}
                            className="bg-kb-muted border border-kb-black px-2 py-0.5 font-mono text-xs uppercase"
                          >
                            {factor}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-8">
          {/* Meetrix Score */}
          <div className="border-3 border-kb-black shadow-brutal-lg bg-kb-white p-8 text-center">
            <div className={`font-display font-black text-8xl leading-none mb-2 ${scoreColor}`}>
              {stats.meetrix_score}
            </div>
            <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-4 flex items-center justify-center gap-2">
              MEETRIX SCORE
              <InfoTooltip text="Overall meeting health score (0–100). Combines waste levels, focus time, decision quality, and cascade chains. 86–100 = Healthy · 66–85 = Needs Attention · 0–65 = Critical Waste." side="top" />
            </div>
            <span
              className={`${verdictColor} border-2 border-kb-black px-4 py-2 font-mono font-bold text-xs uppercase tracking-widest inline-block mb-4`}
            >
              {verdict}
            </span>
            {results.executive_report && (
              <p className="font-sans text-sm text-kb-black/80 leading-relaxed mt-2">
                {results.executive_report.summary.slice(0, 200)}
              </p>
            )}
          </div>

          {/* Executive Report Preview */}
          {results.executive_report && results.executive_report.key_findings.length > 0 && (
            <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
              <h2 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
                KEY FINDINGS
              </h2>
              <ol className="space-y-2">
                {results.executive_report.key_findings.slice(0, 5).map((finding, idx) => (
                  <li
                    key={idx}
                    className="border-l-4 border-kb-lavender pl-3 py-1 font-sans text-sm text-kb-black"
                  >
                    <span className="font-bold text-kb-black/50 mr-2">{idx + 1}.</span>
                    {finding}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Made with Bob
