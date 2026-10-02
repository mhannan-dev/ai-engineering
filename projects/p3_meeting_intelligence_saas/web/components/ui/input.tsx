import React, { forwardRef } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, icon, ...props }, ref) => {
    return (
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
            {icon}
          </div>
        )}
        <input
          className={`w-full bg-white/5 border border-white/10 rounded-xl text-white text-sm outline-none transition-colors focus:border-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed ${
            icon ? 'py-3 pr-3 pl-10' : 'p-3'
          } ${className || ''}`}
          ref={ref}
          {...props}
        />
      </div>
    );
  }
);
Input.displayName = 'Input';
