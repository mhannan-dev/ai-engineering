"use client";

import { useState } from "react";

export function PasswordField({
  value,
  onChange,
  autoComplete = "current-password",
  minLength,
  disabled = false,
}: {
  value: string;
  onChange: (value: string) => void;
  autoComplete?: "current-password" | "new-password";
  minLength?: number;
  disabled?: boolean;
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <label
        htmlFor="password"
        className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
      >
        Password
      </label>
      <div className="relative mt-1">
        <input
          id="password"
          name="password"
          type={visible ? "text" : "password"}
          autoComplete={autoComplete}
          required
          minLength={minLength}
          maxLength={128}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
          className="block w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 pr-11 text-zinc-900 placeholder-zinc-400 shadow-sm transition-colors focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:placeholder-zinc-500 dark:focus:border-zinc-400 dark:focus:ring-zinc-400 sm:text-sm"
          placeholder="••••••••"
        />
        <button
          type="button"
          onClick={() => setVisible((current) => !current)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          className="absolute inset-y-0 right-0 flex items-center px-3 text-zinc-500 hover:text-zinc-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-inset focus-visible:outline-zinc-500 dark:text-zinc-400 dark:hover:text-zinc-200"
        >
          {visible ? (
            <svg
              aria-hidden="true"
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.9 5.2A11.7 11.7 0 0112 5c5 0 8.3 4.1 9.5 6.2a1.6 1.6 0 010 1.6 14.4 14.4 0 01-3.2 3.7M6.2 6.2a14.7 14.7 0 00-3.7 5 1.6 1.6 0 000 1.6C3.7 14.9 7 19 12 19c1.3 0 2.5-.3 3.6-.8"
              />
            </svg>
          ) : (
            <svg
              aria-hidden="true"
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.5 12s3.3-7 9.5-7 9.5 7 9.5 7-3.3 7-9.5 7-9.5-7-9.5-7z"
              />
              <circle cx="12" cy="12" r="3" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
