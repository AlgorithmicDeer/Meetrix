/**
 * Kawaii-Brutalism Card component.
 */

import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  sticker?: string;
}

export function Card({ children, className = '', sticker }: CardProps) {
  return (
    <div className={`bg-kb-white border-3 border-kb-black p-6 shadow-brutal-md relative ${className}`}>
      {sticker && (
        <span className="absolute top-2 right-2 font-mono text-kb-black text-xs">
          {sticker}
        </span>
      )}
      {children}
    </div>
  );
}

// Made with Bob
