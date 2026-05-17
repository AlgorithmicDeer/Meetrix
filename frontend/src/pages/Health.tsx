/**
 * Health Page - Meeting type breakdown, action items, health scores, anomalies.
 */

import { Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';
import { InfoTooltip } from '@/components/ui/InfoTooltip';
import type { MeetingClassification } from '@/types/api';

const TYPE_COLORS: Record<string, string> = {
  standup: 'bg-kb-mint',
  planning: 'bg-kb-lavender',
  decision: 'bg-kb-peach',
  'status-update': 'bg-kb-pink',
  brainstorm: 'bg-kb-lavender',
  '1:1': 'bg-kb-white',
  social: 'bg-kb-mint',
};

const SEVERITY_BORDER: Record<string, string> = {
  high: 'border-l-kb-coral',
  medium: 'border-l-kb-peach',
  low: 'border-l-kb-lavender',
};

const SEVERITY_BG: Record<string, string> = {
  high: 'bg-kb-coral',
  medium: 'bg-kb-peach',
  low: 'bg-kb-lavender',
};

function truncateEmail(email: string): string {
  return email.length > 28 ? email.slice(0, 25) + '...' : email;
}

export function Health() {
  const { results } = useSession();
  const meetingTitleMap = new Map<string, string>(
    (results?.meetings ?? []).map((m) => [m.meeting_id, m.title])
  );

  if (!results || results.status !== 'complete') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
          {results?.status === 'processing' ? 'ANALYSIS IN PROGRESS...' : 'RUN AN ANALYSIS TO SEE HEALTH DATA'}
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

  // Section 1: Meeting type breakdown
  const typeGroups = results.meeting_classifications.reduce<
    Record<MeetingClassification['meeting_type'], MeetingClassification[]>
  >((acc, c) => {
    if (!acc[c.meeting_type]) acc[c.meeting_type] = [];
    acc[c.meeting_type].push(c);
    return acc;
  }, {} as Record<MeetingClassification['meeting_type'], MeetingClassification[]>);

  const allTypes: MeetingClassification['meeting_type'][] = [
    'standup', 'planning', 'decision', 'status-update', 'brainstorm', '1:1', 'social',
  ];

  // Average health score per type
  const avgHealthByType = (type: string): number | null => {
    if (!results.meeting_health_scores.length) return null;
    const typeIds = new Set((typeGroups[type as MeetingClassification['meeting_type']] ?? []).map((c) => c.meeting_id));
    const relevant = results.meeting_health_scores.filter((h) => typeIds.has(h.meeting_id));
    if (!relevant.length) return null;
    return relevant.reduce((sum, h) => sum + h.overall_health_score, 0) / relevant.length;
  };

  // Section 3: Health score aggregates
  const hs = results.meeting_health_scores;
  const hasAgendaCount = hs.filter((h) => h.has_agenda).length;
  const durationAppropriateCount = hs.filter((h) => h.duration_appropriate).length;
  const avgAttendeeFit =
    hs.length > 0
      ? hs.reduce((sum, h) => sum + h.attendee_fit_score, 0) / hs.length
      : 0;

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between mb-2">
        <h1 className="font-display font-black text-3xl uppercase">HEALTH</h1>
      </div>
      <p className="font-sans text-sm text-kb-black/60 mb-6 max-w-2xl">
        Meeting Health Score (0–10) measures whether each meeting follows best practices: a clear agenda, an appropriate duration for its type, and the right number of attendees. It is separate from Waste Score — a meeting can be low-cost but still poorly structured.
      </p>

      {/* Section 1: Meeting Type Breakdown */}
      {results.meeting_classifications.length > 0 ? (
        <div>
          <h2 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
            MEETING TYPE BREAKDOWN
          </h2>
          <div className="grid grid-cols-3 md:grid-cols-4 gap-4">
            {allTypes.map((type) => {
              const count = (typeGroups[type] ?? []).length;
              if (count === 0) return null;
              const avgHealth = avgHealthByType(type);
              return (
                <div
                  key={type}
                  className="border-3 border-kb-black shadow-brutal-md bg-kb-white p-4"
                >
                  <div className="font-display font-black text-4xl text-kb-black mb-1">
                    {count}
                  </div>
                  <span
                    className={`${TYPE_COLORS[type] ?? 'bg-kb-muted'} border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase inline-block mb-2`}
                  >
                    {type}
                  </span>
                  {avgHealth !== null && (
                    <div className="font-mono text-xs text-kb-black/50 uppercase tracking-widest">
                      AVG HEALTH {(avgHealth * 10).toFixed(1)}/10
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="border-3 border-kb-black border-dashed bg-kb-muted p-8 text-center">
          <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/40">
            NO MEETING CLASSIFICATIONS AVAILABLE
          </p>
        </div>
      )}

      {/* Section 2: Action Items */}
      {results.action_items.length > 0 ? (
        <div>
          <div className="flex items-center gap-4 mb-4">
            <h2 className="font-display font-black text-xl uppercase text-kb-black">
              ACTION ITEMS
            </h2>
            <span className="bg-kb-lavender border-2 border-kb-black px-3 py-1 font-mono font-bold text-xs uppercase shadow-brutal-sm">
              {results.action_items.length} TOTAL
            </span>
          </div>
          <div className="border-3 border-kb-black shadow-brutal-md overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-kb-black text-kb-white">
                  <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                    DESCRIPTION
                  </th>
                  <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                    ASSIGNEE
                  </th>
                  <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">
                    MEETING
                  </th>
                  <th className="px-4 py-3 text-left font-mono font-bold text-xs uppercase tracking-widest">
                    DONE
                  </th>
                </tr>
              </thead>
              <tbody>
                {results.action_items.map((item, idx) => {
                  const rowBg =
                    item.followed_through === true
                      ? 'bg-kb-mint'
                      : item.followed_through === false
                      ? 'bg-kb-coral/20'
                      : 'bg-kb-white';
                  return (
                    <tr
                      key={idx}
                      className={`${rowBg} border-b-2 border-kb-black last:border-b-0`}
                    >
                      <td className="px-4 py-3 border-r-2 border-kb-black font-sans text-sm text-kb-black">
                        {item.description}
                      </td>
                      <td className="px-4 py-3 border-r-2 border-kb-black font-mono text-xs text-kb-black">
                        {item.assignee_email
                          ? truncateEmail(item.assignee_email)
                          : 'Unassigned'}
                      </td>
                      <td className="px-4 py-3 border-r-2 border-kb-black font-mono text-xs text-kb-black truncate max-w-[160px]" title={meetingTitleMap.get(item.meeting_id) ?? item.meeting_id}>
                        {meetingTitleMap.get(item.meeting_id) ?? `...${item.meeting_id.slice(-8)}`}
                      </td>
                      <td className="px-4 py-3">
                        {item.followed_through === true && (
                          <span className="bg-kb-mint border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase">
                            DONE
                          </span>
                        )}
                        {item.followed_through === false && (
                          <span className="bg-kb-coral border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase">
                            MISSED
                          </span>
                        )}
                        {item.followed_through === null && (
                          <span className="bg-kb-muted border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase">
                            UNKNOWN
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="border-3 border-kb-black border-dashed bg-kb-muted p-6 text-center">
          <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/40">
            NO ACTION ITEMS AVAILABLE
          </p>
        </div>
      )}

      {/* Section 3: Health Score Aggregates */}
      {hs.length > 0 ? (
        <div>
          <h2 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
            HEALTH SCORES
          </h2>
          <div className="grid grid-cols-3 gap-6">
            {/* Has Agenda */}
            <div className="border-3 border-kb-black shadow-brutal-md p-6 bg-kb-white">
              <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-2 flex items-center gap-1">
                HAS AGENDA
                <InfoTooltip text="Meetings with notes longer than 30 characters are considered to have an agenda. No agenda = no shared context, wasted ramp-up time." side="top" />
              </p>
              <p className="font-display font-black text-4xl text-kb-black mb-3">
                {hasAgendaCount}/{hs.length}
              </p>
              <div className="border-2 border-kb-black h-4 relative overflow-hidden">
                <div
                  className="h-full bg-kb-mint"
                  style={{ width: `${hs.length ? (hasAgendaCount / hs.length) * 100 : 0}%` }}
                />
              </div>
              <p className="font-mono text-xs text-kb-black/50 mt-1 uppercase">
                {hs.length ? ((hasAgendaCount / hs.length) * 100).toFixed(0) : 0}% OF MEETINGS
              </p>
            </div>

            {/* Duration Appropriate */}
            <div className="border-3 border-kb-black shadow-brutal-md p-6 bg-kb-white">
              <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-2 flex items-center gap-1">
                DURATION APPROPRIATE
                <InfoTooltip text="Whether the meeting duration falls in the ideal range for its type. E.g. standups: 5–30 min, 1:1s: 20–60 min, planning: 45–180 min. Meetings outside this range are likely padded or rushed." side="top" />
              </p>
              <p className="font-display font-black text-4xl text-kb-black mb-3">
                {durationAppropriateCount}/{hs.length}
              </p>
              <div className="border-2 border-kb-black h-4 relative overflow-hidden">
                <div
                  className="h-full bg-kb-lavender"
                  style={{
                    width: `${hs.length ? (durationAppropriateCount / hs.length) * 100 : 0}%`,
                  }}
                />
              </div>
              <p className="font-mono text-xs text-kb-black/50 mt-1 uppercase">
                {hs.length ? ((durationAppropriateCount / hs.length) * 100).toFixed(0) : 0}% OF MEETINGS
              </p>
            </div>

            {/* Avg Attendee Fit */}
            <div className="border-3 border-kb-black shadow-brutal-md p-6 bg-kb-white">
              <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-2 flex items-center gap-1">
                AVG ATTENDEE FIT
                <InfoTooltip text="How well the attendee count matched the ideal for the meeting type. 10/10 = perfect size. Lower scores mean the meeting was too large or too small for its purpose." side="top" />
              </p>
              <p className="font-display font-black text-4xl text-kb-black mb-3">
                {(avgAttendeeFit * 10).toFixed(1)}/10
              </p>
              <div className="border-2 border-kb-black h-4 relative overflow-hidden">
                <div
                  className={`h-full ${
                    avgAttendeeFit < 0.5 ? 'bg-kb-coral' : avgAttendeeFit < 0.7 ? 'bg-kb-peach' : 'bg-kb-mint'
                  }`}
                  style={{ width: `${avgAttendeeFit * 100}%` }}
                />
              </div>
              <p className="font-mono text-xs text-kb-black/50 mt-1 uppercase">
                ACROSS {hs.length} MEETINGS
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="border-3 border-kb-black border-dashed bg-kb-muted p-6 text-center">
          <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/40">
            NO HEALTH SCORES AVAILABLE
          </p>
        </div>
      )}

      {/* Section 4: Anomalies */}
      {results.anomalies.length > 0 ? (
        <div>
          <h2 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
            ANOMALIES DETECTED
          </h2>
          <div>
            {results.anomalies.map((anomaly, idx) => (
              <div
                key={idx}
                className={`border-l-4 ${SEVERITY_BORDER[anomaly.severity] ?? 'border-l-kb-lavender'} bg-kb-white border-2 border-kb-black shadow-brutal-sm p-4 mb-3`}
                style={{
                  borderLeftColor:
                    anomaly.severity === 'high'
                      ? '#FF8FA3'
                      : anomaly.severity === 'medium'
                      ? '#FFD4B8'
                      : '#C8B8F8',
                }}
              >
                <div className="flex items-start gap-3 flex-wrap">
                  <span
                    className={`${SEVERITY_BG[anomaly.severity] ?? 'bg-kb-lavender'} border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase flex-shrink-0`}
                  >
                    {anomaly.severity}
                  </span>
                  <span className="bg-kb-muted border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs uppercase flex-shrink-0">
                    {anomaly.anomaly_type}
                  </span>
                  <p className="font-sans text-sm text-kb-black flex-1">
                    {anomaly.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="border-3 border-kb-black border-dashed bg-kb-muted p-6 text-center">
          <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/40">
            NO ANOMALIES DETECTED
          </p>
        </div>
      )}
    </div>
  );
}

// Made with Bob
