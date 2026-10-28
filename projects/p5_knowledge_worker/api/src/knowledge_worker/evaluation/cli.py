"""CLI command to run the retrieval evaluation and ablation benchmark."""

from __future__ import annotations

import argparse

from knowledge_worker.config import get_settings
from knowledge_worker.evaluation.dataset import load_eval_dataset
from knowledge_worker.evaluation.runner import run_retrieval_benchmark
from knowledge_worker.services.container import Container


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format an ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(val))

    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_str = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

    lines = [separator, header_str, separator]
    for row in rows:
        line = "| " + " | ".join(val.ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
        lines.append(line)
    lines.append(separator)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="P5 Knowledge Worker Retrieval Ablation Benchmark")
    parser.add_argument("--k", type=int, default=5, help="Cutoff rank for Recall and nDCG (default: 5)")
    parser.add_argument("--user-id", type=str, default=None, help="User ID (defaults to LOCAL_USER_ID)")
    parser.add_argument("--dataset", type=str, default=None, help="Path to eval_dataset.json")
    args = parser.parse_args()

    settings = get_settings()
    user_id = args.user_id or settings.LOCAL_USER_ID

    print("\n🔍 Loading Evaluation Dataset...")
    dataset = load_eval_dataset(args.dataset)
    print(f"Loaded {len(dataset)} queries (Answerable: {sum(1 for q in dataset if q.is_answerable)}, Unanswerable: {sum(1 for q in dataset if not q.is_answerable)}).")

    print("\n⚡ Initializing Hybrid Retriever & Services Container...")
    container = Container(settings)

    try:
        print(f"\n🚀 Running Retrieval Benchmark against user '{user_id}' across 4 variants...")
        report = run_retrieval_benchmark(container.retriever, user_id=user_id, dataset=dataset, k=args.k)

        headers = ["Variant", f"Recall@{args.k}", "MRR", f"nDCG@{args.k}", "Avg Latency (ms)"]
        rows = []
        for name in ["dense", "sparse", "fused", "reranked"]:
            m = report.variants[name]
            rows.append([
                name.upper(),
                f"{m.mean_recall_at_5:.4f}",
                f"{m.mrr:.4f}",
                f"{m.mean_ndcg_at_5:.4f}",
                f"{m.avg_latency_ms:.1f}",
            ])

        print("\n" + "=" * 65)
        print("          P5 HYBRID RETRIEVAL ABLATION SCOREBOARD")
        print("=" * 65)
        print(format_table(headers, rows))

        print("\n📂 Category Recall Breakdown:")
        cat_headers = ["Category"] + [v.upper() for v in ["dense", "sparse", "fused", "reranked"]]
        all_categories = sorted({cat for v in report.variants.values() for cat in v.category_recall})
        cat_rows = []
        for cat in all_categories:
            cat_row = [cat]
            for v in ["dense", "sparse", "fused", "reranked"]:
                cat_val = report.variants[v].category_recall.get(cat, 0.0)
                cat_row.append(f"{cat_val:.4f}")
            cat_rows.append(cat_row)
        print(format_table(cat_headers, cat_rows))
        print("=" * 65 + "\n")

    finally:
        container.shutdown()


if __name__ == "__main__":
    main()
