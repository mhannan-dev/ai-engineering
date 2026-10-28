export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${units[unit]}`;
}

const relative = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

/** "just now", "5 minutes ago", "yesterday"... The API sends naive UTC timestamps. */
export function formatRelative(iso: string, now: number = Date.now()): string {
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(iso);
  const time = new Date(hasZone ? iso : `${iso}Z`).getTime();
  const seconds = Math.round((time - now) / 1000);
  const abs = Math.abs(seconds);
  if (abs < 45) return "just now";
  if (abs < 3600) return relative.format(Math.round(seconds / 60), "minute");
  if (abs < 86400) return relative.format(Math.round(seconds / 3600), "hour");
  return relative.format(Math.round(seconds / 86400), "day");
}

const LANGUAGE_LABELS: Record<string, string> = {
  en: "English",
  bn: "বাংলা",
  mixed: "Mixed",
  unknown: "Unknown",
};

export function formatLanguage(code: string | null): string {
  if (!code) return "—";
  return LANGUAGE_LABELS[code] ?? code;
}
