/**
 * Schedule Page - Smart meeting scheduler (coming soon preview).
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';

const FEATURES = [
  {
    icon: '🔮',
    title: 'Waste Prediction',
    desc: 'Before you book, see the estimated waste probability based on your team\'s historical patterns.',
  },
  {
    icon: '⏰',
    title: 'Focus-Time Aware Slots',
    desc: 'Proposed slots avoid fragmenting deep-work blocks and flag attendees already in meeting overload.',
  },
  {
    icon: '📋',
    title: 'Auto-Generated Agenda',
    desc: 'Enter your purpose and required decisions — get a structured agenda drafted for you.',
  },
  {
    icon: '👥',
    title: 'Right-Size Your Attendees',
    desc: 'Identifies who truly needs to attend vs. who can get an async summary.',
  },
  {
    icon: '📅',
    title: 'iCal Export',
    desc: 'One click to add the proposed meeting to your calendar with agenda pre-filled.',
  },
];

export function Schedule() {
  const { sessionId } = useSession();
  const [purpose, setPurpose] = useState('');
  const [attendees, setAttendees] = useState('');
  const [duration, setDuration] = useState(60);
  const [clicked, setClicked] = useState(false);

  const handleGenerate = () => {
    setClicked(true);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <h1 className="font-display font-black text-3xl uppercase">SCHEDULE A MEETING</h1>
          <span className="bg-kb-lavender border-2 border-kb-black px-3 py-1 font-mono font-bold text-xs uppercase tracking-widest shadow-brutal-sm">
            COMING SOON
          </span>
        </div>
        {!sessionId && (
          <Link
            to="/settings"
            className="font-mono text-xs uppercase tracking-widest text-kb-black/50 hover:text-kb-black underline"
          >
            Load an analysis first
          </Link>
        )}
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Left: Form preview */}
        <div className="bg-kb-white border-3 border-kb-black shadow-brutal-lg p-8">
          <h2 className="font-display font-black text-2xl uppercase mb-2 text-kb-black">
            MEETING DETAILS
          </h2>
          <p className="font-sans text-sm text-kb-black/50 mb-6">
            This feature is in development. Preview the form below.
          </p>

          <div className="space-y-5 opacity-75">
            <div className="flex flex-col gap-2">
              <label className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
                MEETING PURPOSE
              </label>
              <textarea
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="What decisions need to be made?"
                rows={3}
                className="border-2 border-kb-black bg-kb-white px-4 py-3 font-sans text-base text-kb-black focus:outline-none resize-none"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
                ATTENDEES
              </label>
              <textarea
                value={attendees}
                onChange={(e) => setAttendees(e.target.value)}
                placeholder="One email per line — only invite decision-makers"
                rows={3}
                className="border-2 border-kb-black bg-kb-white px-4 py-3 font-mono text-sm text-kb-black focus:outline-none resize-none"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
                DURATION (MINUTES)
              </label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                min={15}
                step={15}
                className="border-2 border-kb-black bg-kb-white px-4 py-3 font-mono text-base text-kb-black focus:outline-none"
              />
            </div>
          </div>

          {clicked ? (
            <div className="mt-6 border-3 border-kb-lavender bg-kb-lavender/20 p-6 text-center">
              <div className="text-3xl mb-3">🚧</div>
              <p className="font-display font-black text-lg uppercase text-kb-black mb-2">
                FEATURE IN DEVELOPMENT
              </p>
              <p className="font-sans text-sm text-kb-black/70">
                Smart scheduling is being built. It will analyse your team's historical waste patterns and focus-time data to propose the optimal slot, right-size the attendee list, and auto-draft an agenda.
              </p>
            </div>
          ) : (
            <button
              onClick={handleGenerate}
              className="mt-6 w-full bg-kb-pink border-3 border-kb-black shadow-brutal-md font-display font-black text-xl py-4 uppercase hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
            >
              GENERATE PROPOSAL
            </button>
          )}
        </div>

        {/* Right: Feature showcase */}
        <div className="space-y-4">
          <div className="bg-kb-peach border-3 border-kb-black shadow-brutal-md p-6">
            <h2 className="font-display font-black text-xl uppercase mb-1 text-kb-black">
              WHAT THIS FEATURE WILL DO
            </h2>
            <p className="font-sans text-sm text-kb-black/70 mb-4">
              Smart scheduling powered by your analysis data — not just calendar availability.
            </p>
          </div>

          {FEATURES.map((f, i) => (
            <div
              key={i}
              className="bg-kb-white border-3 border-kb-black shadow-brutal-sm p-5 flex items-start gap-4"
            >
              <span className="text-2xl flex-shrink-0">{f.icon}</span>
              <div>
                <div className="font-display font-black text-base uppercase text-kb-black mb-1">
                  {f.title}
                </div>
                <p className="font-sans text-sm text-kb-black/70 leading-relaxed">{f.desc}</p>
              </div>
            </div>
          ))}

          <div className="bg-kb-mint border-3 border-kb-black shadow-brutal-md p-5">
            <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/60 mb-2">
              WANT THIS BUILT FIRST?
            </p>
            <p className="font-sans text-sm text-kb-black/80">
              Run an analysis and use the{' '}
              <Link to="/ask" className="underline font-bold">
                Ask
              </Link>{' '}
              feature to get scheduling recommendations from your own data right now.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Made with Bob
