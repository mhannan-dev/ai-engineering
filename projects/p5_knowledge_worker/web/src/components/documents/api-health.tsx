"use client";

import { useEffect, useState } from "react";

import { API_BASE_URL, getHealth } from "@/lib/api";

type Health = { state: "checking" } | { state: "online"; version: string } | { state: "offline" };

const POLL_MS = 15_000;

export function ApiHealth() {
  const [health, setHealth] = useState<Health>({ state: "checking" });

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const result = await getHealth();
        if (!cancelled) setHealth({ state: "online", version: result.version });
      } catch {
        if (!cancelled) setHealth({ state: "offline" });
      }
    }
    void check();
    const timer = setInterval(check, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const dot =
    health.state === "online"
      ? "bg-emerald-500"
      : health.state === "offline"
        ? "bg-rose-500"
        : "bg-zinc-400 animate-pulse";
  const label =
    health.state === "online"
      ? `API online · v${health.version}`
      : health.state === "offline"
        ? "API offline"
        : "Checking API…";

  return (
    <a
      id="api-health"
      href={`${API_BASE_URL}/docs`}
      target="_blank"
      rel="noreferrer"
      title={`${API_BASE_URL} (open Swagger)`}
      className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-700 transition-colors hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:border-zinc-700 dark:hover:bg-zinc-800"
    >
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden />
      {label}
    </a>
  );
}
