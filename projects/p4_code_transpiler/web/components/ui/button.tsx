import React, { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
}

/** Primary gradient action button with an optional loading spinner. */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', isLoading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={isLoading || disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 px-6 py-3 text-[0.95rem] font-semibold text-white shadow-[0_4px_15px_rgba(99,102,241,0.35)] transition-all duration-200 hover:-translate-y-[1px] hover:shadow-[0_6px_22px_rgba(99,102,241,0.5)] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 ${className}`}
      {...props}
    >
      {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  )
);
Button.displayName = 'Button';
