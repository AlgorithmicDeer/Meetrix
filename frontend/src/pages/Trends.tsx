/**
 * Trends Page - Executive summary, waste distribution chart, focus time chart, ROI projection.
 */

import { Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { useSession } from '@/contexts/SessionContext';
import type { WasteScore, FocusTimeScore } from '@/types/api';

const CATEGORY_COLORS: Record<string, string> = {
  'High Waste': '#FF8FA3',
  'Medium Waste': '#FFD4B8',
  'Low Waste': '#A8EED4',
  'High Value': '#C8B8F8',
};

function wasteBarColor(category: WasteScore['category']): string {
  return CATEGORY_COLORS[category] ?? '#C8B8F8';
}

function focusBarColor(fp: number): string {
  if (fp < 0.2) return '#FF8FA3';
  if (fp < 0.35) return '#FFD4B8';
  return '#A8EED4';
}

interface WasteTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: WasteScore & { label: string; title: string } }>;
}

function WasteTooltip({ active, payload }: WasteTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-4 font-mono text-xs max-w-[200px]">
      <div className="font-bold uppercase mb-2 break-words">{d.title || d.label}</div>
      <div>Cost Factor: {(d.cost_factor * 100).toFixed(0)}%</div>
      <div>Decision Deficit: {(d.decision_deficit * 100).toFixed(0)}%</div>
      <div>Participation: {(d.participation_imbalance * 100).toFixed(0)}%</div>
      <div>Recurrence: {(d.recurrence_staleness * 100).toFixed(0)}%</div>
      <div className="mt-1 font-bold">Composite: {(d.composite_score * 100).toFixed(0)}%</div>
    </div>
  );
}

export function Trends() {
  const { results } = useSession();

  if (!results || results.status !== 'complete') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
          {results?.status === 'processing' ? 'ANALYSIS IN PROGRESS...' : 'RUN AN ANALYSIS TO SEE TRENDS'}
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

  const meetingTitleMap = new Map(
    (results.meetings ?? []).map((m) => [m.meeting_id, m.title])
  );
  const wasteData = results.waste_scores.map((ws) => {
    const title = meetingTitleMap.get(ws.meeting_id) ?? '';
    return {
      ...ws,
      title,
      label: title ? title.slice(0, 11) : ws.meeting_id.slice(-6),
    };
  });

  const focusData = results.focus_scores.map((fs) => ({
    ...fs,
    shortEmail: fs.person_email.slice(0, 10),
  }));

  const report = results.executive_report;
  const roi = results.roi_projection;
  const stats = results.summary_stats;

  const trendIcon =
    report?.trend_direction === 'improving'
      ? '↑'
      : report?.trend_direction === 'worsening'
      ? '↓'
      : '→';

  const trendColor =
    report?.trend_direction === 'improving'
      ? 'bg-kb-mint'
      : report?.trend_direction === 'worsening'
      ? 'bg-kb-coral'
      : 'bg-kb-lavender';

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between mb-2">
        <h1 className="font-display font-black text-3xl uppercase">TRENDS</h1>
      </div>

      {/* Section 1: Executive Summary */}
      {report ? (
        <div className="bg-kb-white border-3 border-kb-black shadow-brutal-lg p-8">
          <div className="flex items-center gap-4 mb-6 flex-wrap">
            <span
              className={`${trendColor} border-2 border-kb-black px-4 py-2 font-mono font-bold text-sm uppercase tracking-widest`}
            >
              TREND: {report.trend_direction.toUpperCase()} {trendIcon}
            </span>
            <span className="font-mono text-xs uppercase tracking-widest text-kb-black/50">
              {report.period}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <div className="bg-kb-peach border-2 border-kb-black p-4">
              <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
                TOTAL COST
              </div>
              <div className="font-display font-black text-3xl text-kb-black">
                ${stats.total_cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </div>
            </div>
            <div className="bg-kb-lavender border-2 border-kb-black p-4">
              <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
                TOTAL MEETINGS
              </div>
              <div className="font-display font-black text-3xl text-kb-black">
                {stats.total_meetings}
              </div>
            </div>
            <div className="bg-kb-mint border-2 border-kb-black p-4">
              <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
                MEETRIX SCORE
              </div>
              <div className="font-display font-black text-3xl text-kb-black">
                {stats.meetrix_score}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="border-3 border-kb-black border-dashed bg-kb-muted p-8 text-center">
          <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/40">
            NO EXECUTIVE REPORT AVAILABLE
          </p>
        </div>
      )}

      {/* Section 2: Waste Score Distribution */}
      {wasteData.length > 0 && (
        <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
          <h2 className="font-display font-black text-xl uppercase mb-6 text-kb-black">
            WASTE SCORE DISTRIBUTION
          </h2>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={wasteData}
              margin={{ top: 8, right: 16, bottom: 60, left: 0 }}
            >
              <XAxis
                dataKey="label"
                tick={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 9, fill: '#000' }}
                tickLine={false}
                axisLine={{ stroke: '#000', strokeWidth: 2 }}
                interval={0}
                angle={-35}
                textAnchor="end"
                height={52}
              />
              <YAxis
                domain={[0, 1]}
                tick={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fill: '#000' }}
                tickLine={false}
                axisLine={{ stroke: '#000', strokeWidth: 2 }}
                tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              />
              <Tooltip content={<WasteTooltip />} />
              <Bar dataKey="composite_score" stroke="#000000" strokeWidth={2}>
                {wasteData.map((entry, idx) => (
                  <Cell key={idx} fill={wasteBarColor(entry.category)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="flex gap-4 mt-4 flex-wrap">
            {Object.entries(CATEGORY_COLORS).map(([label, color]) => (
              <div key={label} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 border-2 border-kb-black flex-shrink-0"
                  style={{ backgroundColor: color }}
                />
                <span className="font-mono text-xs uppercase tracking-widest text-kb-black">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 3: Focus Time by Person */}
      {focusData.length > 0 && (
        <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
          <h2 className="font-display font-black text-xl uppercase mb-6 text-kb-black">
            MEETING HOURS BY PERSON
          </h2>
          <ResponsiveContainer width="100%" height={Math.max(200, focusData.length * 32)}>
            <BarChart
              data={focusData}
              layout="vertical"
              margin={{ top: 0, right: 32, bottom: 0, left: 80 }}
            >
              <XAxis
                type="number"
                tick={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fill: '#000' }}
                tickLine={false}
                axisLine={{ stroke: '#000', strokeWidth: 2 }}
              />
              <YAxis
                type="category"
                dataKey="shortEmail"
                width={80}
                tick={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fill: '#000' }}
                tickLine={false}
                axisLine={{ stroke: '#000', strokeWidth: 2 }}
              />
              <Tooltip
                formatter={(value: number) => [`${value.toFixed(1)} hrs/wk`, 'Meeting Hours']}
                contentStyle={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: 12,
                  border: '3px solid #000',
                  borderRadius: 0,
                  boxShadow: '3px 3px 0 #000',
                }}
              />
              <Bar dataKey="total_meeting_hours" stroke="#000000" strokeWidth={2}>
                {focusData.map((entry: FocusTimeScore & { shortEmail: string }, idx) => (
                  <Cell key={idx} fill={focusBarColor(entry.focus_percentage)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Section 4: ROI Projection */}
      {roi ? (
        <div className="bg-kb-mint border-3 border-kb-black shadow-brutal-md p-8">
          <h2 className="font-display font-black text-xl uppercase mb-6 text-kb-black">
            ROI PROJECTION
          </h2>
          <div className="grid grid-cols-2 gap-8">
            <div>
              <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
                PROJECTED ANNUAL SAVING
              </div>
              <div className="font-display font-black text-5xl text-kb-black mb-4">
                ${roi.projected_annual_saving.toLocaleString()}
              </div>
              <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
                BREAK-EVEN
              </div>
              <div className="font-display font-black text-3xl text-kb-black">
                {roi.weeks_to_break_even} WEEKS
              </div>
            </div>
            <div>
              <div className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black mb-3">
                TOP CHANGES
              </div>
              <ul className="space-y-2 mb-4">
                {roi.top_changes.map((change, i) => (
                  <li key={i} className="flex gap-2 font-sans text-sm text-kb-black">
                    <span className="font-mono font-bold flex-shrink-0">✦</span>
                    {change}
                  </li>
                ))}
              </ul>
              {roi.assumptions.length > 0 && (
                <div>
                  <div className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50 mb-2">
                    ASSUMPTIONS
                  </div>
                  <ul className="space-y-1">
                    {roi.assumptions.map((assumption, i) => (
                      <li key={i} className="font-sans text-xs text-kb-black/60">
                        {assumption}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

// Made with Bob
