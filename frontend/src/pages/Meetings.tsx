/**
 * Meetings Page - Full correlated meeting data table with expandable rows.
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';
import { InfoTooltip } from '@/components/ui/InfoTooltip';
import type {
  WasteScore,
  MeetingClassification,
  Recommendation,
  Intervention,
  MeetingHealth,
  MeetingInfo,
} from '@/types/api';

interface MeetingRow {
  id: string;
  info: MeetingInfo | undefined;
  wasteScore: WasteScore | undefined;
  classification: MeetingClassification | undefined;
  recommendation: Recommendation | undefined;
  intervention: Intervention | undefined;
  health: MeetingHealth | undefined;
  isCascadeOrigin: boolean;
}

type Tab = 'ALL' | 'HIGH WASTE' | 'CASCADE ORIGINS' | 'RECOMMENDATIONS';

const ACTION_COLORS: Record<string, string> = {
  cancel: 'bg-kb-coral',
  shorten: 'bg-kb-peach',
  restructure: 'bg-kb-lavender',
  keep: 'bg-kb-mint',
  merge: 'bg-kb-pink',
};

const CATEGORY_COLORS: Record<string, string> = {
  'High Waste': 'bg-kb-coral',
  'Medium Waste': 'bg-kb-peach',
  'Low Waste': 'bg-kb-lavender',
  'High Value': 'bg-kb-mint',
};

const TYPE_COLORS: Record<string, string> = {
  standup: 'bg-kb-mint',
  planning: 'bg-kb-lavender',
  decision: 'bg-kb-peach',
  'status-update': 'bg-kb-pink',
  brainstorm: 'bg-kb-lavender',
  '1:1': 'bg-kb-white',
  social: 'bg-kb-mint',
};

function formatDate(dt: string): string {
  try {
    return new Date(dt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

function MiniProgressBar({
  label,
  tooltip,
  value,
}: {
  label: string;
  tooltip: string;
  value: number;
}) {
  const fillColor =
    value > 0.7 ? 'bg-kb-coral' : value > 0.4 ? 'bg-kb-peach' : 'bg-kb-mint';
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="font-mono text-xs uppercase tracking-widest text-kb-black/60 w-52 flex-shrink-0 flex items-center gap-1.5">
        {label}
        <InfoTooltip text={tooltip} side="right" />
      </span>
      <div className="flex-1 border-2 border-kb-black h-4 relative overflow-hidden">
        <div
          className={`h-full ${fillColor} transition-all duration-300`}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="font-mono text-xs font-bold text-kb-black w-10 text-right flex-shrink-0">
        {(value * 100).toFixed(0)}%
      </span>
    </div>
  );
}

export function Meetings() {
  const { results } = useSession();
  const [activeTab, setActiveTab] = useState<Tab>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  if (!results || results.status !== 'complete') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
          {results?.status === 'processing' ? 'ANALYSIS IN PROGRESS...' : 'RUN AN ANALYSIS TO SEE MEETING DATA'}
        </p>
        <Link
          to="/settings"
          className="border-2 border-kb-black bg-kb-pink px-6 py-3 font-mono font-bold text-sm uppercase tracking-widest shadow-brutal-sm hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
        >
          {results?.status === 'processing' ? 'View Progress' : 'Go to Settings'}
        </Link>
      </div>
    );
  }

  const meetingMap = new Map<string, MeetingInfo>(
    (results.meetings ?? []).map((m) => [m.meeting_id, m])
  );

  const cascadeOriginIds = new Set(
    results.cascade_chains.map((c) => c.origin_meeting_id)
  );

  const allIds = new Set<string>([
    ...(results.meetings ?? []).map((m) => m.meeting_id),
    ...results.waste_scores.map((w) => w.meeting_id),
    ...results.meeting_classifications.map((c) => c.meeting_id),
    ...results.recommendations.map((r) => r.meeting_id),
    ...results.interventions.map((i) => i.meeting_id),
    ...results.meeting_health_scores.map((h) => h.meeting_id),
  ]);

  const rows: MeetingRow[] = Array.from(allIds).map((id) => ({
    id,
    info: meetingMap.get(id),
    wasteScore: results.waste_scores.find((w) => w.meeting_id === id),
    classification: results.meeting_classifications.find((c) => c.meeting_id === id),
    recommendation: results.recommendations.find((r) => r.meeting_id === id),
    intervention: results.interventions.find((i) => i.meeting_id === id),
    health: results.meeting_health_scores.find((h) => h.meeting_id === id),
    isCascadeOrigin: cascadeOriginIds.has(id),
  }));

  // Sort by waste score desc
  rows.sort((a, b) => (b.wasteScore?.composite_score ?? 0) - (a.wasteScore?.composite_score ?? 0));

  const filteredRows = useMemo(() => {
    let filtered = rows;
    switch (activeTab) {
      case 'HIGH WASTE':
        filtered = rows.filter((r) => r.wasteScore && r.wasteScore.composite_score > 0.6);
        break;
      case 'CASCADE ORIGINS':
        filtered = rows.filter((r) => r.isCascadeOrigin);
        break;
      case 'RECOMMENDATIONS':
        filtered = rows.filter((r) => r.recommendation !== undefined);
        break;
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      filtered = filtered.filter((r) =>
        r.info?.title.toLowerCase().includes(q) ||
        r.id.toLowerCase().includes(q) ||
        r.classification?.meeting_type.toLowerCase().includes(q)
      );
    }
    return filtered;
  }, [rows, activeTab, search]);

  const tabs: Tab[] = ['ALL', 'HIGH WASTE', 'CASCADE ORIGINS', 'RECOMMENDATIONS'];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display font-black text-3xl uppercase">MEETINGS</h1>
        <span className="font-mono text-xs uppercase tracking-widest text-kb-black/50">
          {allIds.size} MEETINGS ANALYZED
        </span>
      </div>

      {/* Search + Tabs */}
      <div className="flex items-end gap-4 mb-0 flex-wrap">
        <div className="border-b-3 border-kb-black flex">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`border-r-2 border-kb-black px-5 py-3 font-mono font-bold text-xs uppercase tracking-widest transition-colors duration-75 ${
                activeTab === tab
                  ? 'bg-kb-black text-kb-white'
                  : 'bg-kb-white text-kb-black hover:bg-kb-lavender'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="flex-1 min-w-[200px] mb-0 pb-0 border-b-3 border-kb-black">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search meetings..."
            className="w-full border-0 bg-kb-white px-4 py-3 font-mono text-sm focus:outline-none"
          />
        </div>
      </div>

      {/* Table */}
      <div className="border-3 border-kb-black border-t-0 shadow-brutal-md overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-kb-black text-kb-white">
              <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10 min-w-[200px]">
                MEETING
              </th>
              <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                DATE
              </th>
              <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                <span className="flex items-center gap-1.5">
                  WASTE
                  <InfoTooltip text="How wasteful this meeting was (0–100%). Combines: salary cost relative to team norms, missing decisions, unequal participation, and whether a recurring series has gone stale." side="top" />
                </span>
              </th>
              <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                <span className="flex items-center gap-1.5">
                  CATEGORY
                  <InfoTooltip text="High Waste = eliminate or restructure · Medium Waste = improve · Low Waste = acceptable · High Value = protect and replicate." side="top" />
                </span>
              </th>
              <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                TYPE
              </th>
              <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                ACTION
              </th>
              <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest">
                <span className="flex items-center gap-1.5">
                  HEALTH
                  <InfoTooltip text="Meeting health score (0–10). Based on whether it had an agenda, whether the duration matched the type, and how many relevant attendees were present." side="top" />
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-12 font-mono text-xs uppercase tracking-widest text-kb-black/40">
                  NO MEETINGS MATCH THIS FILTER
                </td>
              </tr>
            )}
            {filteredRows.map((row) => {
              const composite = row.wasteScore?.composite_score ?? 0;
              const rowBg =
                composite > 0.7
                  ? 'bg-kb-coral/10'
                  : composite > 0.4
                  ? 'bg-kb-peach/10'
                  : 'bg-kb-white';
              const isExpanded = expandedId === row.id;
              const title = row.info?.title ?? `...${row.id.slice(-8)}`;

              return (
                <>
                  <tr
                    key={row.id}
                    className={`${rowBg} border-b-2 border-kb-black cursor-pointer hover:brightness-95 transition-all duration-75`}
                    onClick={() => setExpandedId(isExpanded ? null : row.id)}
                  >
                    {/* Title */}
                    <td className="px-4 py-3 border-r-2 border-kb-black">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-bold text-sm text-kb-black truncate max-w-xs" title={title}>
                          {title}
                        </span>
                        {row.isCascadeOrigin && (
                          <span className="bg-kb-peach border border-kb-black px-1 font-mono text-xs uppercase flex-shrink-0">
                            CASCADE
                          </span>
                        )}
                        {row.info?.is_recurring && (
                          <span className="bg-kb-lavender border border-kb-black px-1 font-mono text-xs uppercase flex-shrink-0">
                            REC
                          </span>
                        )}
                      </div>
                      {row.info && (
                        <div className="font-mono text-xs text-kb-black/40 mt-0.5">
                          {row.info.duration_minutes}min · {row.info.attendee_count} people
                        </div>
                      )}
                    </td>

                    {/* Date */}
                    <td className="px-4 py-3 border-r-2 border-kb-black font-mono text-xs text-kb-black/60 whitespace-nowrap">
                      {row.info ? formatDate(row.info.start_datetime) : '—'}
                    </td>

                    {/* Waste score */}
                    <td className="px-4 py-3 border-r-2 border-kb-black font-mono font-bold text-sm">
                      {row.wasteScore ? `${(composite * 100).toFixed(0)}%` : '—'}
                    </td>

                    {/* Category */}
                    <td className="px-4 py-3 border-r-2 border-kb-black">
                      {row.wasteScore ? (
                        <span
                          className={`${
                            CATEGORY_COLORS[row.wasteScore.category] ?? 'bg-kb-muted'
                          } border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase whitespace-nowrap`}
                        >
                          {row.wasteScore.category}
                        </span>
                      ) : (
                        <span className="text-kb-black/30 font-mono text-xs">—</span>
                      )}
                    </td>

                    {/* Type */}
                    <td className="px-4 py-3 border-r-2 border-kb-black">
                      {row.classification ? (
                        <span
                          className={`${
                            TYPE_COLORS[row.classification.meeting_type] ?? 'bg-kb-muted'
                          } border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase whitespace-nowrap`}
                        >
                          {row.classification.meeting_type}
                        </span>
                      ) : (
                        <span className="text-kb-black/30 font-mono text-xs">—</span>
                      )}
                    </td>

                    {/* Recommendation action */}
                    <td className="px-4 py-3 border-r-2 border-kb-black">
                      {row.recommendation ? (
                        <span
                          className={`${
                            ACTION_COLORS[row.recommendation.recommended_action] ?? 'bg-kb-muted'
                          } border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase`}
                        >
                          {row.recommendation.recommended_action}
                        </span>
                      ) : (
                        <span className="text-kb-black/30 font-mono text-xs">—</span>
                      )}
                    </td>

                    {/* Health */}
                    <td className="px-4 py-3">
                      {row.health ? (
                        <div className="flex items-center gap-2">
                          <div className="border-2 border-kb-black h-3 w-16 relative overflow-hidden">
                            <div
                              className={`h-full ${row.health.overall_health_score >= 0.7 ? 'bg-kb-mint' : row.health.overall_health_score >= 0.4 ? 'bg-kb-peach' : 'bg-kb-coral'}`}
                              style={{ width: `${row.health.overall_health_score * 100}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-xs text-kb-black">
                            {(row.health.overall_health_score * 10).toFixed(1)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-kb-black/30 font-mono text-xs">—</span>
                      )}
                    </td>
                  </tr>

                  {isExpanded && (
                    <tr key={`${row.id}-expanded`}>
                      <td colSpan={7} className="bg-kb-cream border-b-2 border-kb-black px-6 py-6">
                        <div className="grid grid-cols-2 gap-8">
                          {row.wasteScore && (
                            <div>
                              <h3 className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black mb-3">
                                WASTE DIMENSIONS
                              </h3>
                              <MiniProgressBar
                                label="Cost Factor"
                                tooltip="How expensive this meeting was relative to similar ones — based on number of attendees, their seniority, and duration. High = disproportionately costly."
                                value={row.wasteScore.cost_factor}
                              />
                              <MiniProgressBar
                                label="Decision Deficit"
                                tooltip="Did the meeting produce decisions? High = few or no decisions recorded. Meetings without outcomes are the root cause of cascade chains."
                                value={row.wasteScore.decision_deficit}
                              />
                              <MiniProgressBar
                                label="Participation Imbalance"
                                tooltip="Were people speaking equally? High = most attendees were passive observers who could have received an email summary instead."
                                value={row.wasteScore.participation_imbalance}
                              />
                              <MiniProgressBar
                                label="Recurrence Staleness"
                                tooltip="For recurring meetings: is this series still needed? High = the meeting recurs regularly but decisions and engagement have declined over time."
                                value={row.wasteScore.recurrence_staleness}
                              />
                            </div>
                          )}
                          <div className="space-y-4">
                            {row.recommendation && (
                              <div>
                                <h3 className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black mb-2">
                                  RECOMMENDATION
                                </h3>
                                <p className="font-sans text-sm text-kb-black bg-kb-white border-2 border-kb-black p-3">
                                  {row.recommendation.reasoning}
                                </p>
                              </div>
                            )}
                            {row.intervention && (
                              <div>
                                <h3 className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black mb-2">
                                  SUGGESTED AGENDA
                                </h3>
                                <ol className="space-y-1 bg-kb-white border-2 border-kb-black p-3">
                                  {row.intervention.suggested_agenda.map((item, i) => (
                                    <li key={i} className="font-sans text-sm text-kb-black flex gap-2">
                                      <span className="font-mono font-bold text-kb-black/50">{i + 1}.</span>
                                      {item}
                                    </li>
                                  ))}
                                </ol>
                                {row.intervention.alternative_format && (
                                  <p className="font-sans text-xs text-kb-black/60 mt-2 italic">
                                    Alternative: {row.intervention.alternative_format}
                                  </p>
                                )}
                              </div>
                            )}
                            {row.health && (
                              <div className="space-y-2">
                                <div className="flex gap-3 flex-wrap">
                                  {row.health.has_agenda ? (
                                    <span className="bg-kb-mint border-2 border-kb-black px-2 py-1 font-mono text-xs uppercase">
                                      ✓ HAS AGENDA
                                    </span>
                                  ) : (
                                    <span className="bg-kb-coral border-2 border-kb-black px-2 py-1 font-mono text-xs uppercase">
                                      ✗ NO AGENDA
                                    </span>
                                  )}
                                  {row.health.duration_appropriate ? (
                                    <span className="bg-kb-mint border-2 border-kb-black px-2 py-1 font-mono text-xs uppercase">
                                      ✓ DURATION OK
                                    </span>
                                  ) : (
                                    <span className="bg-kb-peach border-2 border-kb-black px-2 py-1 font-mono text-xs uppercase">
                                      ✗ DURATION OFF
                                    </span>
                                  )}
                                  <span className="bg-kb-muted border-2 border-kb-black px-2 py-1 font-mono text-xs uppercase">
                                    ATTENDEE FIT {(row.health.attendee_fit_score * 10).toFixed(1)}/10
                                  </span>
                                </div>
                                <p className="font-sans text-xs text-kb-black/50">
                                  Health score combines agenda presence (50%), appropriate duration for meeting type (30%), and right-sized attendee list (20%).
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Made with Bob
