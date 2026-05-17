/**
 * Kawaii-Brutalism Progress Bar component.
 */

interface ProgressBarProps {
  percentage: number;
  color?: 'pink' | 'lavender' | 'mint' | 'peach' | 'coral';
  className?: string;
}

export function ProgressBar({ 
  percentage, 
  color = 'lavender',
  className = '' 
}: ProgressBarProps) {
  const colorClasses = {
    pink: 'bg-kb-pink',
    lavender: 'bg-kb-lavender',
    mint: 'bg-kb-mint',
    peach: 'bg-kb-peach',
    coral: 'bg-kb-coral',
  };

  return (
    <div className={`w-full border-2 border-kb-black bg-kb-muted h-8 ${className}`}>
      <div
        className={`h-full ${colorClasses[color]} border-r-2 border-kb-black transition-all duration-300`}
        style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
      />
    </div>
  );
}

// Made with Bob
