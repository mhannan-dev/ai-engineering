/**
 * The signed-in user's bearer token, kept in localStorage so a reload stays signed in.
 * Storage can be unavailable (private mode, blocked site data), so every access is guarded
 * and the app falls back to asking the user to sign in again.
 */

const TOKEN_KEY = "kw.access_token";
export const SESSION_EVENT = "kw:session-change";

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function notify() {
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function saveToken(token: string) {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Signed in for this page only; a reload will ask again.
  }
  notify();
}

export function clearSession() {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Nothing stored.
  }
  notify();
}
