/**
 * InfoTooltip - "?" icon that shows explanatory text on hover.
 * Use next to any technical term to give first-time users context.
 */

interface InfoTooltipProps {
  text: string;
  /** 'left' | 'right' controls which side the bubble opens toward. Default 'right' */
  side?: 'left' | 'right' | 'top';
  wide?: boolean;
}

export function InfoTooltip({ text, side = 'top', wide = false }: InfoTooltipProps) {
  const posClass =
    side === 'left'
      ? 'right-full top-1/2 -translate-y-1/2 mr-2'
      : side === 'right'
      ? 'left-full top-1/2 -translate-y-1/2 ml-2'
      : 'bottom-full left-1/2 -translate-x-1/2 mb-2';

  return (
    <span className="relative group inline-flex items-center flex-shrink-0">
      <span className="w-[14px] h-[14px] rounded-full border-2 border-kb-black/40 bg-kb-white text-[9px] font-mono font-black text-kb-black/50 flex items-center justify-center cursor-help select-none hover:bg-kb-black hover:text-kb-white hover:border-kb-black transition-colors duration-75">
        ?
      </span>
      <div
        className={`absolute ${posClass} z-50 ${wide ? 'w-72' : 'w-56'} bg-kb-black text-kb-white text-xs font-sans leading-relaxed p-3 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150 shadow-brutal-sm`}
      >
        {text}
        {side === 'top' && (
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-kb-black" />
        )}
        {side === 'left' && (
          <div className="absolute left-full top-1/2 -translate-y-1/2 border-4 border-transparent border-l-kb-black" />
        )}
        {side === 'right' && (
          <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-kb-black" />
        )}
      </div>
    </span>
  );
}

// Made with Bob
