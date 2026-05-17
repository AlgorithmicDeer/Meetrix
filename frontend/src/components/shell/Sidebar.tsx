/**
 * Kawaii-Brutalism Sidebar with mascot, Meetrix Score, and emoji nav.
 */

import { NavLink } from 'react-router-dom';

interface SidebarProps {
  meetrixScore: number;
}

export function Sidebar({ meetrixScore }: SidebarProps) {
  const getScoreColor = (score: number) => {
    if (score >= 86) return 'text-kb-lavender';
    if (score >= 66) return 'text-kb-mint';
    if (score >= 41) return 'text-kb-peach';
    return 'text-kb-coral';
  };

  const navItems = [
    { path: '/', label: 'Overview', emoji: '🏠' },
    { path: '/schedule', label: 'Schedule', emoji: '📅' },
    { path: '/ask', label: 'Ask', emoji: '💬' },
    { path: '/meetings', label: 'Meetings', emoji: '📋' },
    { path: '/people', label: 'People', emoji: '👥' },
    { path: '/network', label: 'Network', emoji: '🕸️' },
    { path: '/health', label: 'Health', emoji: '🏥' },
    { path: '/trends', label: 'Trends', emoji: '📈' },
    { path: '/reports', label: 'Reports', emoji: '📄' },
    { path: '/settings', label: 'Settings', emoji: '⚙️' },
  ];

  const scoreDisplay = meetrixScore === 0 ? '—' : meetrixScore;

  return (
    <aside className="w-64 bg-kb-black border-r-3 border-kb-black min-h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b-2 border-white/10">
        <h1 className="font-display font-black text-2xl uppercase tracking-widest text-kb-pink">
          MEETRIX
        </h1>
      </div>

      {/* Mascot */}
      <div className="px-6 py-4 border-b-2 border-white/10">
        <div className="text-center">
          <span className="font-mono text-lg text-kb-lavender">✦(•‿•)✦</span>
        </div>
      </div>

      {/* Meetrix Score Widget */}
      <div className="px-6 py-8 border-b-2 border-white/10">
        <div className="text-center">
          <div className={`font-display font-black text-6xl ${meetrixScore === 0 ? 'text-white/30' : getScoreColor(meetrixScore)}`}>
            {scoreDisplay}
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-white/60 mt-2">
            MEETRIX SCORE
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `w-full px-6 py-3 font-mono font-bold text-sm uppercase tracking-widest border-b border-white/10 flex items-center gap-3 transition-colors duration-75 ${
                isActive
                  ? 'bg-kb-pink text-kb-black border-l-4 border-kb-black'
                  : 'text-white/80 hover:bg-kb-lavender hover:text-kb-black'
              }`
            }
          >
            <span className="text-base leading-none">{item.emoji}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}

        {/* New Analysis Link */}
        <div className="border-t-2 border-white/20 mt-2 pt-2">
          <NavLink
            to="/settings"
            className="w-full px-6 py-3 font-mono font-bold text-xs uppercase tracking-widest border-b border-white/10 flex items-center gap-3 text-kb-mint/80 hover:text-kb-mint hover:bg-white/5 transition-colors duration-75"
          >
            <span className="text-base leading-none">✦</span>
            <span>New Analysis</span>
          </NavLink>
        </div>
      </nav>

      {/* Privacy Strip */}
      <div className="p-4 border-t-2 border-white/10">
        <div className="flex flex-wrap gap-2 justify-center">
          <span className="bg-kb-mint border-2 border-kb-black px-2 py-1 font-mono font-bold text-xs uppercase">
            LOCAL AI
          </span>
          <span className="bg-kb-mint border-2 border-kb-black px-2 py-1 font-mono font-bold text-xs uppercase">
            LOCAL DB
          </span>
          <span className="bg-kb-mint border-2 border-kb-black px-2 py-1 font-mono font-bold text-xs uppercase">
            ZERO CLOUD
          </span>
        </div>
      </div>
    </aside>
  );
}

// Made with Bob
