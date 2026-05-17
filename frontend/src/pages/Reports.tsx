/**
 * Reports Page - Full executive report with copy utilities.
 */

import { Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';

export function Reports() {
  const { results } = useSession();

  if (!results || results.status !== 'complete' || !results.executive_report) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
          {results?.status === 'processing' ? 'ANALYSIS IN PROGRESS...' : 'RUN AN ANALYSIS TO SEE YOUR EXECUTIVE REPORT'}
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

  const report = results.executive_report;
  const roi = results.roi_projection;
  const stats = results.summary_stats;

  const scoreColor =
    stats.meetrix_score >= 86
      ? 'bg-kb-lavender'
      : stats.meetrix_score >= 66
      ? 'bg-kb-mint'
      : stats.meetrix_score >= 41
      ? 'bg-kb-peach'
      : 'bg-kb-coral';

  const trendColor =
    report.trend_direction === 'improving'
      ? 'bg-kb-mint'
      : report.trend_direction === 'worsening'
      ? 'bg-kb-coral'
      : 'bg-kb-lavender';

  const trendIcon =
    report.trend_direction === 'improving' ? '↑' : report.trend_direction === 'worsening' ? '↓' : '→';

  const generateMarkdown = () => {
    const lines: string[] = [
      '# Meeting Analysis Report',
      '',
      `## Period: ${report.period}`,
      '',
      '## Summary',
      '',
      report.summary,
      '',
      '## Key Findings',
      '',
      ...report.key_findings.map((f, i) => `${i + 1}. ${f}`),
      '',
      '## Top Recommendations',
      '',
      ...report.top_recommendations.map((r, i) => `${i + 1}. ${r}`),
      '',
      '## Metrics',
      '',
      `- Total Cost: $${report.total_cost.toLocaleString()}`,
      `- Total Meetings: ${report.total_meetings}`,
      `- Meetrix Score: ${report.meetrix_score}`,
      `- Trend: ${report.trend_direction}`,
      `- Data Residency: ${report.data_residency}`,
    ];

    if (roi) {
      lines.push(
        '',
        '## ROI Projection',
        '',
        `- Projected Annual Saving: $${roi.projected_annual_saving.toLocaleString()}`,
        `- Break-even: ${roi.weeks_to_break_even} weeks`,
        '',
        '### Top Changes',
        '',
        ...roi.top_changes.map((c) => `- ${c}`),
      );
    }

    return lines.join('\n');
  };

  const generatePlainText = () => {
    const lines: string[] = [
      'MEETING ANALYSIS REPORT',
      '='.repeat(40),
      '',
      `PERIOD: ${report.period}`,
      '',
      'SUMMARY',
      '-'.repeat(20),
      report.summary,
      '',
      'KEY FINDINGS',
      '-'.repeat(20),
      ...report.key_findings.map((f, i) => `${i + 1}. ${f}`),
      '',
      'TOP RECOMMENDATIONS',
      '-'.repeat(20),
      ...report.top_recommendations.map((r, i) => `${i + 1}. ${r}`),
      '',
      'METRICS',
      '-'.repeat(20),
      `Total Cost: $${report.total_cost.toLocaleString()}`,
      `Total Meetings: ${report.total_meetings}`,
      `Meetrix Score: ${report.meetrix_score}`,
      `Trend: ${report.trend_direction}`,
      `Data Residency: ${report.data_residency}`,
    ];

    if (roi) {
      lines.push(
        '',
        'ROI PROJECTION',
        '-'.repeat(20),
        `Projected Annual Saving: $${roi.projected_annual_saving.toLocaleString()}`,
        `Break-even: ${roi.weeks_to_break_even} weeks`,
        '',
        'Top Changes:',
        ...roi.top_changes.map((c) => `  - ${c}`),
      );
    }

    return lines.join('\n');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).catch(() => {
      // Fallback for environments without clipboard API
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <h1 className="font-display font-black text-3xl uppercase">REPORTS</h1>
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-mono text-xs uppercase tracking-widest text-kb-black/50">
            {report.period}
          </span>
          <span
            className={`${scoreColor} border-2 border-kb-black px-3 py-1 font-mono font-bold text-xs uppercase shadow-brutal-sm`}
          >
            SCORE: {report.meetrix_score}
          </span>
          <span
            className={`${trendColor} border-2 border-kb-black px-3 py-1 font-mono font-bold text-xs uppercase shadow-brutal-sm`}
          >
            {report.trend_direction.toUpperCase()} {trendIcon}
          </span>
        </div>
      </div>

      {/* Executive Report Card */}
      <div className="border-3 border-kb-black shadow-brutal-lg bg-kb-white p-12 mb-8">
        <h2 className="font-display font-black text-4xl uppercase mb-2 text-kb-black">
          EXECUTIVE BRIEFING
        </h2>
        <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-8">
          {report.period}
        </p>

        {/* Summary */}
        <div className="border-l-4 border-kb-lavender pl-6 mb-8">
          <p className="font-sans text-base leading-relaxed text-kb-black">
            {report.summary}
          </p>
        </div>

        {/* Key Findings */}
        {report.key_findings.length > 0 && (
          <div className="mb-8">
            <h3 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
              KEY FINDINGS
            </h3>
            <ol className="space-y-3">
              {report.key_findings.map((finding, idx) => (
                <li key={idx} className="flex gap-4 py-3 border-b-2 border-kb-black last:border-b-0">
                  <div className="w-8 h-8 bg-kb-lavender border-2 border-kb-black flex items-center justify-center font-mono font-black text-sm flex-shrink-0">
                    {idx + 1}
                  </div>
                  <p className="font-sans text-sm text-kb-black leading-relaxed pt-1">
                    {finding}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Top Recommendations */}
        {report.top_recommendations.length > 0 && (
          <div>
            <h3 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
              TOP RECOMMENDATIONS
            </h3>
            <ol className="space-y-3">
              {report.top_recommendations.map((rec, idx) => (
                <li key={idx} className="flex gap-4 py-3 border-b-2 border-kb-black last:border-b-0">
                  <div className="w-8 h-8 bg-kb-pink border-2 border-kb-black flex items-center justify-center font-mono font-black text-sm flex-shrink-0">
                    {idx + 1}
                  </div>
                  <p className="font-sans text-sm text-kb-black leading-relaxed pt-1">
                    {rec}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-kb-peach border-3 border-kb-black shadow-brutal-md p-6">
          <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
            TOTAL COST
          </p>
          <p className="font-display font-black text-3xl text-kb-black">
            ${stats.total_cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="bg-kb-lavender border-3 border-kb-black shadow-brutal-md p-6">
          <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
            TOTAL MEETINGS
          </p>
          <p className="font-display font-black text-3xl text-kb-black">
            {stats.total_meetings}
          </p>
        </div>
        <div className="bg-kb-mint border-3 border-kb-black shadow-brutal-md p-6">
          <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
            DATA RESIDENCY
          </p>
          <p className="font-display font-black text-3xl text-kb-black uppercase">
            {report.data_residency || 'LOCAL'}
          </p>
        </div>
      </div>

      {/* ROI Projection */}
      {roi && (
        <div className="bg-kb-mint border-3 border-kb-black shadow-brutal-md p-8 mb-8">
          <h2 className="font-display font-black text-xl uppercase mb-6 text-kb-black">
            ROI PROJECTION
          </h2>
          <div className="grid grid-cols-2 gap-8">
            <div>
              <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
                ANNUAL SAVING
              </p>
              <p className="font-display font-black text-5xl text-kb-black mb-4">
                ${roi.projected_annual_saving.toLocaleString()}
              </p>
              <p className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-1">
                BREAK-EVEN
              </p>
              <p className="font-display font-black text-3xl text-kb-black">
                {roi.weeks_to_break_even} WEEKS
              </p>
            </div>
            <div>
              <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black mb-3">
                TOP CHANGES
              </p>
              <ul className="space-y-2 mb-4">
                {roi.top_changes.map((change, i) => (
                  <li key={i} className="flex gap-2 font-sans text-sm text-kb-black">
                    <span className="font-mono font-bold flex-shrink-0 text-kb-black/60">✦</span>
                    {change}
                  </li>
                ))}
              </ul>
              {roi.assumptions.length > 0 && (
                <>
                  <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50 mb-2">
                    ASSUMPTIONS
                  </p>
                  <ul className="space-y-1">
                    {roi.assumptions.map((a, i) => (
                      <li key={i} className="font-sans text-xs text-kb-black/60">
                        {a}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Copy Buttons */}
      <div className="flex gap-4">
        <button
          onClick={() => copyToClipboard(generateMarkdown())}
          className="border-3 border-kb-black bg-kb-lavender shadow-brutal-sm px-6 py-3 font-mono font-bold text-sm uppercase tracking-widest hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
        >
          COPY MARKDOWN
        </button>
        <button
          onClick={() => copyToClipboard(generatePlainText())}
          className="border-3 border-kb-black bg-kb-white shadow-brutal-sm px-6 py-3 font-mono font-bold text-sm uppercase tracking-widest hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
        >
          COPY PLAIN TEXT
        </button>
      </div>
    </div>
  );
}

// Made with Bob
