"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { FormField } from "@/components/auth/form-field";
import { PasswordField } from "@/components/auth/password-field";
import { SubmitButton } from "@/components/auth/submit-button";
import { ApiError, demoLogin, login } from "@/lib/api";

export function SignInForm() {
  const { signIn, demoLoginEnabled } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      signIn(await login(email, password));
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't sign in right now.");
      setBusy(false);
    }
  }

  async function handleDemoLogin() {
    setBusy(true);
    setError(null);
    try {
      signIn(await demoLogin());
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't sign in right now.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={(event) => void handleSubmit(event)} className="mt-8 space-y-6">
      <div className="space-y-4">
        <FormField
          id="email"
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          disabled={busy}
        />
        <PasswordField value={password} onChange={setPassword} disabled={busy} />
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      <SubmitButton disabled={busy}>{busy ? "Signing in…" : "Sign in"}</SubmitButton>
      {demoLoginEnabled && (
        <button
          type="button"
          onClick={() => void handleDemoLogin()}
          disabled={busy}
          className="flex w-full justify-center rounded-lg border border-zinc-300 px-4 py-2.5 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-900 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-800 dark:focus-visible:outline-zinc-50"
        >
          {busy ? "Signing in…" : "Continue with demo account"}
        </button>
      )}
    </form>
  );
}
