"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { FormField } from "@/components/auth/form-field";
import { PasswordField } from "@/components/auth/password-field";
import { SubmitButton } from "@/components/auth/submit-button";
import { ApiError, register } from "@/lib/api";

const MIN_PASSWORD = 8;

export function SignUpForm() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      signIn(await register(name.trim(), email, password));
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create the account right now.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={(event) => void handleSubmit(event)} className="mt-8 space-y-6">
      <div className="space-y-4">
        <FormField
          id="name"
          label="Name"
          autoComplete="name"
          maxLength={100}
          value={name}
          onChange={(event) => setName(event.target.value)}
          disabled={busy}
        />
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
        <div>
          <PasswordField
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            minLength={MIN_PASSWORD}
            disabled={busy}
          />
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
            At least {MIN_PASSWORD} characters.
          </p>
        </div>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      <SubmitButton disabled={busy}>{busy ? "Creating account…" : "Create account"}</SubmitButton>
    </form>
  );
}
