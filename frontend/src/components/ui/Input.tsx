/**
 * Kawaii-Brutalism Input component.
 */

import { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function Input({ label, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-2">
      {label && (
        <label className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
          {label}
        </label>
      )}
      <input
        className={`
          border-2 border-kb-black bg-kb-white
          px-4 py-3 font-sans font-medium text-base text-kb-black
          focus:outline-none focus:border-3 focus:shadow-brutal-sm
          transition-all duration-75
          disabled:bg-kb-muted disabled:cursor-not-allowed
          ${className}
        `}
        {...props}
      />
    </div>
  );
}

interface TextareaProps extends InputHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  rows?: number;
}

export function Textarea({ label, rows = 4, className = '', ...props }: TextareaProps) {
  return (
    <div className="flex flex-col gap-2">
      {label && (
        <label className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
          {label}
        </label>
      )}
      <textarea
        rows={rows}
        className={`
          border-2 border-kb-black bg-kb-white
          px-4 py-3 font-sans font-medium text-base text-kb-black
          focus:outline-none focus:border-3 focus:shadow-brutal-sm
          transition-all duration-75
          disabled:bg-kb-muted disabled:cursor-not-allowed
          resize-none
          ${className}
        `}
        {...(props as any)}
      />
    </div>
  );
}

// Made with Bob
