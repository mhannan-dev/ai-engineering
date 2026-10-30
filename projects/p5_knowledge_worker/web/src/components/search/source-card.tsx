import type { SearchResultChunk } from "@/lib/api";

function location(chunk: SearchResultChunk): string {
  const parts = [chunk.document_filename];
  if (chunk.page !== null) parts.push(`Page ${chunk.page}`);
  return parts.join(" · ");
}

function RankPill({ label, rank }: { label: string; rank: number | null }) {
  if (rank === null) return null;
  return (
    <span className="rounded-md bg-zinc-100 px-1.5 py-0.5 font-mono text-[11px] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
      {label} #{rank}
    </span>
  );
}

/** One retrieved passage with where it came from and how each retriever ranked it. */
export function SourceCard({
  chunk,
  position,
  compact = false,
}: {
  chunk: SearchResultChunk;
  position?: number;
  compact?: boolean;
}) {
  return (
    <article className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
        {position !== undefined && (
          <span className="rounded-md bg-zinc-900 px-1.5 py-0.5 font-mono text-[11px] text-white dark:bg-zinc-100 dark:text-zinc-900">
            {position}
          </span>
        )}
        <span className="font-medium text-zinc-800 dark:text-zinc-200">{location(chunk)}</span>
        {chunk.heading && (
          <span className="max-w-[16rem] truncate" title={chunk.heading}>
            {chunk.heading}
          </span>
        )}
        <span className="ml-auto font-mono tabular-nums" title="Score">
          {chunk.score.toFixed(3)}
        </span>
      </div>
      <p
        className={`whitespace-pre-wrap text-sm leading-relaxed text-zinc-800 dark:text-zinc-200 ${
          compact ? "line-clamp-3" : "line-clamp-6"
        }`}
      >
        {chunk.text}
      </p>
      {!compact && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          <RankPill label="Dense" rank={chunk.dense_rank} />
          <RankPill label="BM25" rank={chunk.sparse_rank} />
          <RankPill label="RRF" rank={chunk.fused_rank} />
          <RankPill label="Rerank" rank={chunk.rerank_rank} />
        </div>
      )}
    </article>
  );
}
