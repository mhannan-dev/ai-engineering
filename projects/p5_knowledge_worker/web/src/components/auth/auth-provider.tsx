"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { getAuthConfig, getMe, type TokenResponse, type User } from "@/lib/api";
import { SESSION_EVENT, clearSession, getToken, saveToken } from "@/lib/session";

export type AuthState =
  | { status: "loading" }
  | { status: "disabled" } // API runs with AUTH_ENABLED=false: one local user, no sign-in
  | { status: "unreachable" } // API is down; pages show their own connection errors
  | { status: "signed-out" }
  | { status: "signed-in"; user: User };

interface AuthContextValue {
  state: AuthState;
  signIn: (response: TokenResponse) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>.");
  return value;
}

export const PUBLIC_PATHS = ["/login", "/register"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  // State is set only in the promise callbacks, so effects can call this without cascading renders.
  const check = useCallback(
    () =>
      getAuthConfig().then(
        (config) => {
          if (!config.enabled) return setState({ status: "disabled" });
          if (!getToken()) return setState({ status: "signed-out" });
          return getMe().then(
            (user) => setState({ status: "signed-in", user }),
            () => setState({ status: getToken() ? "unreachable" : "signed-out" }),
          );
        },
        () => setState({ status: "unreachable" }),
      ),
    [],
  );

  useEffect(() => {
    void check();
    // Fires on sign-in, sign-out and when the API rejects an expired token.
    const onChange = () => void check();
    window.addEventListener(SESSION_EVENT, onChange);
    return () => window.removeEventListener(SESSION_EVENT, onChange);
  }, [check]);

  const signIn = useCallback((response: TokenResponse) => {
    setState({ status: "signed-in", user: response.user });
    saveToken(response.access_token);
  }, []);

  const signOut = useCallback(() => {
    clearSession();
  }, []);

  return (
    <AuthContext.Provider value={{ state, signIn, signOut }}>
      <AuthGate state={state}>{children}</AuthGate>
    </AuthContext.Provider>
  );
}

/** Sends signed-out visitors to /login and signed-in ones away from it. */
function AuthGate({ state, children }: { state: AuthState; children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = PUBLIC_PATHS.includes(pathname);
  const redirect =
    !isPublic && state.status === "signed-out"
      ? "/login"
      : isPublic && (state.status === "signed-in" || state.status === "disabled")
        ? "/"
        : null;

  useEffect(() => {
    if (redirect) router.replace(redirect);
  }, [redirect, router]);

  if (redirect || (!isPublic && state.status === "loading")) {
    return (
      <div className="flex flex-1 items-center justify-center py-24" aria-busy="true">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-zinc-100" />
      </div>
    );
  }
  return children;
}
