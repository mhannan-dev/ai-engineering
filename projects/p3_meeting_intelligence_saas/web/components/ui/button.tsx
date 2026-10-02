import React, { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'glass';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', isLoading, children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center gap-2 font-semibold text-[0.95rem] px-6 py-3 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';
    
    const variants = {
      primary: 'bg-gradient-to-br from-indigo-500 to-cyan-500 text-white shadow-[0_4px_15px_rgba(99,102,241,0.35)] hover:-translate-y-[1px] hover:shadow-[0_6px_22px_rgba(99,102,241,0.5)] hover:brightness-110',
      secondary: 'bg-white/5 text-white border border-white/10 hover:bg-white/10 hover:border-white/20',
      ghost: 'bg-transparent text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 text-sm px-3 py-1',
      glass: 'bg-white/5 text-white/70 hover:text-white hover:bg-white/10'
    };

    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={`${baseStyles} ${variants[variant]} ${className}`}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
