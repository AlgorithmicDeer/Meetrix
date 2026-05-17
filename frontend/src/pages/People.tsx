/**
 * People Page - Focus time analysis and network insights per person.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';
import { InfoTooltip } from '@/components/ui/InfoTooltip';
import type { FocusTimeScore } from '@/types/api';

type SortMode = 'overloaded' | 'meetings' | 'alpha';

function truncateEmail(email: string): string {
  return email.length > 28 ? email.slice(0, 25) + '...' : email;
}

function avatarColor(email: string): string {
  const idx = email.charCodeAt(0) % 4;
  return ['bg-kb-pink', 'bg-kb-lavender', 'bg-kb-mint', 'bg-kb-peach'][idx];
}

function PersonCard({ person }: { person: FocusTimeScore }) {
  const isOverloaded = person.total_meeting_hours > 15;
  const initials = person.person_email
    .split(/[@._]/)
    .filter(Boolean)
    .slice(0, 1)
    .map((s) => s.charAt(0).toUpperCase())
    .join('');

  const barColor =
    person.focus_percentage < 0.2
      ? 'bg-kb-coral'
      : person.focus_percentage < 0.35
      ? 'bg-kb-peach'
      : person.focus_percentage < 0.5
      ? 'bg-kb-lavender'
      : 'bg-kb-mint';

  const barPct = Math.round(person.focus_percentage * 100);

  const borderClass = isOverloaded
    ? 'border-kb-coral shadow-brutal-md'
    : 'border-kb-black shadow-brutal-md';

  return (
    <div
      className={`bg-kb-white border-3 ${borderClass} p-6`}
    >
      {/* Avatar + name row */}
      <div className="flex items-center gap-3 mb-3">
        <div
          className={`w-14 h-14 border-3 border-kb-black flex items-center justify-center font-display font-black text-2xl flex-shrink-0 ${avatarColor(person.person_email)}`}
        >
          {initials || '?'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-sm text-kb-black truncate" title={person.person_email}>
            {truncateEmail(person.person_email)}
          </div>
          {isOverloaded && (
            <span className="bg-kb-coral border-2 border-kb-black px-2 py-0.5 font-mono text-xs uppercase inline-block mt-1">
              OVERLOADED
            </span>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <div className="bg-kb-muted border-2 border-kb-black px-3 py-1 text-center flex-1 min-w-0">
          <div className="font-display font-black text-lg leading-none">
            {person.total_meeting_hours.toFixed(1)}
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-kb-black/50 flex items-center justify-center gap-1">
            HRS IN MEETINGS
            <InfoTooltip text="Total hours in meetings over the analysis period. Above 15 hours flags this person as overloaded (~5hrs/week)." side="top" />
          </div>
        </div>
        <div className="bg-kb-muted border-2 border-kb-black px-3 py-1 text-center flex-1 min-w-0">
          <div className="font-display font-black text-lg leading-none">
            {person.focus_blocks_remaining}
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-kb-black/50 flex items-center justify-center gap-1">
            FOCUS BLOCKS
            <InfoTooltip text="Number of uninterrupted 90-minute+ gaps in their calendar where they can do deep work." side="top" />
          </div>
        </div>
        <div className="bg-kb-muted border-2 border-kb-black px-3 py-1 text-center flex-1 min-w-0">
          <div className="font-display font-black text-lg leading-none">
            {person.longest_focus_block_minutes}m
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-kb-black/50 flex items-center justify-center gap-1">
            LONGEST GAP
            <InfoTooltip text="The longest consecutive meeting-free block in their calendar. Under 90 minutes makes deep work very difficult." side="top" />
          </div>
        </div>
      </div>

      {/* Focus percentage bar */}
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-mono text-xs uppercase tracking-widest text-kb-black/50 flex items-center gap-1">
          FOCUS TIME
          <InfoTooltip text="Percentage of working time NOT in meetings (measured on days with meetings). The lower this is, the less time available for deep independent work." side="top" />
        </span>
      </div>
      <div className="border-2 border-kb-black h-6 relative overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all duration-300`}
          style={{ width: `${barPct}%` }}
        />
        {barPct > 30 && (
          <span className="absolute inset-0 flex items-center justify-center font-mono font-bold text-xs text-kb-black">
            {barPct}% FOCUS
          </span>
        )}
        {barPct <= 30 && (
          <span className="absolute inset-y-0 right-2 flex items-center font-mono font-bold text-xs text-kb-black">
            {barPct}%
          </span>
        )}
      </div>
    </div>
  );
}

export function People() {
  const { results } = useSession();
  const [sortMode, setSortMode] = useState<SortMode>('overloaded');

  if (!results || results.status !== 'complete') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
          {results?.status === 'processing' ? 'ANALYSIS IN PROGRESS...' : 'RUN AN ANALYSIS TO SEE PEOPLE DATA'}
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

  const sortedPeople = [...results.focus_scores].sort((a, b) => {
    if (sortMode === 'overloaded') return a.focus_percentage - b.focus_percentage;
    if (sortMode === 'meetings') return b.total_meeting_hours - a.total_meeting_hours;
    return a.person_email.localeCompare(b.person_email);
  });

  const sortButtons: { mode: SortMode; label: string }[] = [
    { mode: 'overloaded', label: 'MOST OVERLOADED' },
    { mode: 'meetings', label: 'MOST MEETINGS' },
    { mode: 'alpha', label: 'ALPHABETICAL' },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display font-black text-3xl uppercase">PEOPLE & FOCUS TIME</h1>
        <span className="bg-kb-lavender border-2 border-kb-black px-4 py-2 font-mono font-bold text-xs uppercase shadow-brutal-sm">
          {results.focus_scores.length} PEOPLE
        </span>
      </div>

      {/* Sort controls */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <span className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50">
          SORT BY:
        </span>
        {sortButtons.map(({ mode, label }) => (
          <button
            key={mode}
            onClick={() => setSortMode(mode)}
            className={`border-2 border-kb-black px-4 py-2 font-mono font-bold text-xs uppercase tracking-widest transition-all duration-75 ${
              sortMode === mode
                ? 'bg-kb-black text-kb-white'
                : 'bg-kb-white text-kb-black hover:bg-kb-lavender hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none shadow-brutal-sm'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Person cards grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {sortedPeople.map((person) => (
          <PersonCard key={person.person_email} person={person} />
        ))}
      </div>

      {/* Network Graph Summary */}
      {results.network_graph && (
        <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
          <h2 className="font-display font-black text-xl uppercase mb-4 text-kb-black">
            NETWORK INSIGHTS
          </h2>
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-kb-lavender border-2 border-kb-black p-4">
              <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-2">
                MOST CENTRAL PERSON
              </div>
              <div className="font-mono font-bold text-sm text-kb-black truncate">
                {results.network_graph.most_central_person}
              </div>
            </div>
            <div className="bg-kb-coral border-2 border-kb-black p-4">
              <div className="font-mono text-xs uppercase tracking-widest text-kb-black/60 mb-2">
                HIGHEST COST PAIR
              </div>
              <div className="font-mono font-bold text-sm text-kb-black">
                <span className="truncate block">
                  {truncateEmail(results.network_graph.highest_cost_pair[0])}
                </span>
                <span className="text-kb-black/40 font-normal">↔</span>
                <span className="truncate block">
                  {truncateEmail(results.network_graph.highest_cost_pair[1])}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Made with Bob
