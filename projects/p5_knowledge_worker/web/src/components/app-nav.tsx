"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { PUBLIC_PATHS, useAuth } from "@/components/auth/auth-provider";
import { ApiHealth } from "@/components/documents/api-health";

const LINKS = [
  { href: "/", label: "Documents" },
  { href: "/search", label: "Search" },
  { href: "/chat", label: "Ask" },
] as const;

export function AppNav() {
  const pathname = usePathname();
  const { state, signOut } = useAuth();

  if (PUBLIC_PATHS.includes(pathname)) return null;

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Knowledge Worker
          </Link>
          <nav className="flex items-center gap-1" aria-label="Main">
            {LINKS.map((link) => {
              const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={active ? "page" : undefined}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                      : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <ApiHealth />
          {state.status === "signed-in" && (
            <div className="flex items-center gap-2 text-sm">
              <span className="max-w-40 truncate text-zinc-600 dark:text-zinc-400" title={state.user.email}>
                {state.user.name}
              </span>
              <button
                id="sign-out"
                type="button"
                onClick={signOut}
                className="rounded-lg px-2.5 py-1 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
