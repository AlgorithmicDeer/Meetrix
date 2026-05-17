/**
 * Kawaii-Brutalism Loading Spinner.
 */

export function Spinner({ className = '' }: { className?: string }) {
  return (
    <div
      className={`border-3 border-kb-black border-t-kb-lavender w-8 h-8 animate-spin ${className}`}
    />
  );
}

export function LoadingText({ text = 'LOADING...' }: { text?: string }) {
  return (
    <span className="font-mono font-bold text-sm uppercase tracking-widest animate-pulse text-kb-black">
      {text}
    </span>
  );
}

// Made with Bob
