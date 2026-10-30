import type { Metadata } from "next";

import { PageHeader } from "@/components/page-header";
import { SearchWorkspace } from "@/components/search/search-workspace";

export const metadata: Metadata = {
  title: "Search · Enterprise Knowledge Worker",
};

export default function SearchPage() {
  return (
    <main className="flex-1 font-sans">
      <div className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10 sm:px-6">
        <PageHeader
          title="Search"
          description="Hybrid retrieval over your documents. Compare mode shows what dense search, BM25, RRF and the reranker each return."
        />
        <SearchWorkspace />
      </div>
    </main>
  );
}
