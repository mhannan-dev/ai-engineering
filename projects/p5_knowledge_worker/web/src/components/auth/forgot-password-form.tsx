"use client";

import { useState, type FormEvent } from "react";

import { FormField } from "@/components/auth/form-field";
import { SubmitButton } from "@/components/auth/submit-button";
import { requestPasswordReset } from "@/lib/api";

type RequestStatus = "idle" | "loading" | "success" | "error";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<RequestStatus>("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("loading");
    setMessage("");
    try {
      setMessage(await requestPasswordReset(email));
      setStatus("success");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to send a reset link right now.");
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <section
        role="status"
        className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200"
      >
        <p className="font-medium">Check your inbox</p>
        <p className="mt-1">{message}</p>
      </section>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 space-y-6">
      <FormField
        id="email"
        label="Email address"
        type="email"
        autoComplete="email"
        placeholder="you@example.com"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        disabled={status === "loading"}
      />

      {status === "error" && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {message}
        </p>
      )}

      <SubmitButton disabled={status === "loading"}>
        {status === "loading" ? "Sending..." : "Send reset link"}
      </SubmitButton>
    </form>
  );
}
