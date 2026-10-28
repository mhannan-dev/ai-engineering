import type { DocumentStatus } from "@/lib/api";

const STYLES: Record<DocumentStatus, { label: string; className: string; dot: string }> = {
  pending: {
    label: "Pending",
    className:
      "bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/20",
    dot: "bg-amber-500",
  },
  processing: {
    label: "Processing",
    className:
      "bg-sky-50 text-sky-800 ring-sky-600/20 dark:bg-sky-400/10 dark:text-sky-300 dark:ring-sky-400/20",
    dot: "bg-sky-500 animate-pulse",
  },
  indexed: {
    label: "Indexed",
    className:
      "bg-emerald-50 text-emerald-800 ring-emerald-600/20 dark:bg-emerald-400/10 dark:text-emerald-300 dark:ring-emerald-400/20",
    dot: "bg-emerald-500",
  },
  failed: {
    label: "Failed",
    className:
      "bg-rose-50 text-rose-800 ring-rose-600/20 dark:bg-rose-400/10 dark:text-rose-300 dark:ring-rose-400/20",
    dot: "bg-rose-500",
  },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const style = STYLES[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${style.className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} aria-hidden />
      {style.label}
    </span>
  );
}

export function isInFlight(status: DocumentStatus): boolean {
  return status === "pending" || status === "processing";
}
