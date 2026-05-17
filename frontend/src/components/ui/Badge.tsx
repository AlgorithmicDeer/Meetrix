/**
 * Kawaii-Brutalism Badge component for status tags.
 */

import { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'error' | 'warning' | 'info' | 'muted';
  className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variantClasses = {
    default: 'bg-kb-lavender',
    success: 'bg-kb-mint',
    error: 'bg-kb-coral',
    warning: 'bg-kb-peach',
    info: 'bg-kb-pink',
    muted: 'bg-kb-muted',
  };

  return (
    <span
      className={`
        ${variantClasses[variant]}
        border-2 border-kb-black
        px-3 py-1
        font-mono font-bold text-xs uppercase tracking-widest text-kb-black
        shadow-brutal-sm
        inline-block
        ${className}
      `}
    >
      {children}
    </span>
  );
}

// Made with Bob
