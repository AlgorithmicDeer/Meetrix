/**
 * Kawaii-Brutalism Button component.
 * Applies the brutal press interaction with kawaii color fills.
 */

import { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'destructive' | 'success';
  children: ReactNode;
}

export function Button({ 
  variant = 'primary', 
  children, 
  className = '',
  disabled,
  ...props 
}: ButtonProps) {
  const baseClasses = `
    border-3 border-kb-black
    px-6 py-3 font-mono font-bold text-sm uppercase tracking-widest
    shadow-brutal-sm
    transition-all duration-75 cursor-pointer
    disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-kb-muted
  `;

  const variantClasses = {
    primary: 'bg-kb-pink text-kb-black hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none active:translate-x-[3px] active:translate-y-[3px] active:shadow-brutal-none',
    secondary: 'bg-kb-white text-kb-black hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none active:translate-x-[3px] active:translate-y-[3px] active:shadow-brutal-none',
    destructive: 'bg-kb-coral text-kb-black hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none active:translate-x-[3px] active:translate-y-[3px] active:shadow-brutal-none',
    success: 'bg-kb-mint text-kb-black hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none active:translate-x-[3px] active:translate-y-[3px] active:shadow-brutal-none',
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

// Made with Bob
