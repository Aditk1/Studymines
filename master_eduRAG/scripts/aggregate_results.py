#!/usr/bin/env python3
"""
scripts/aggregate_results.py — Aggregate per-variant JSON files into summary.

Corresponds to `scripts.aggregate_results` in run_commands.md §2d, §3d, §4d.
Flags: --emit-markdown, --emit-ablation-table
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

VARIANT_ORDER = [
    "naive_rag",
    "standard_graphrag",
    "plus_c1",
    "plus_c1_c2",
    "plus_c1_c2_c3",
    "full_edurag",
]

VARIANT_DISPLAY = {
    "naive_rag":          "Naive RAG",
    "standard_graphrag":  "Standard GraphRAG",
    "plus_c1":            "+C1",
    "plus_c1_c2":         "+C1+C2",
    "plus_c1_c2_c3":      "+C1+C2+C3",
    "full_edurag":        "Full eduRAG",
}


def load_results(results_dir: str, dataset: str) -> dict[str, dict]:
    """Load all per-variant JSONs for a dataset."""
    loaded: dict[str, dict] = {}
    pattern = str(Path(results_dir) / f"{dataset}_*.json")
    files = glob.glob(pattern)
    for fp in files:
        name = Path(fp).stem  # e.g. "musique_full_edurag"
        variant = name.replace(f"{dataset}_", "")
        with open(fp) as f:
            data = json.load(f)
        loaded[variant] = data
    return loaded


def aggregate(results: dict[str, dict]) -> dict:
    """Compute summary metrics across variants."""
    summary = {}
    for variant, data in results.items():
        s = data.get("summary", data)
        summary[variant] = {
            "n":           s.get("n_queries", 0),
            "rouge_l":     s.get("rouge_l", 0.0),
            "token_f1":    s.get("token_f1", 0.0),
            "exact_match": s.get("exact_match", 0.0),
            "operational": s.get("operational", {}),
            "hop_breakdown": s.get("hop_breakdown", {}),
        }
    return summary


def emit_markdown(summary: dict, dataset: str, out_path: str) -> None:
    lines = [
        f"# {dataset.upper()} — Aggregate Results",
        "",
        "| Variant | ROUGE-L | Token F1 | Exact Match |",
        "|---|---:|---:|---:|",
    ]
    for v in VARIANT_ORDER:
        if v not in summary:
            continue
        s = summary[v]
        lines.append(
            f"| {VARIANT_DISPLAY.get(v, v)} | {s['rouge_l']:.4f} | {s['token_f1']:.4f} | {s['exact_match']:.4f} |"
        )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  📄 Markdown summary → {out_path}")


def emit_ablation_table(summary: dict, dataset: str, out_path: str) -> None:
    """Emit delta-per-contribution table vs naive_rag baseline."""
    baseline_rouge = summary.get("naive_rag", {}).get("rouge_l", 0.0)

    lines = [
        f"# {dataset.upper()} — Ablation Delta Table",
        "",
        "| Contribution | Variant | ROUGE-L | Δ ROUGE-L vs Naive |",
        "|---|---|---:|---:|",
    ]
    prev_rouge = baseline_rouge
    for v in VARIANT_ORDER:
        if v not in summary:
            continue
        s = summary[v]
        delta = s["rouge_l"] - prev_rouge
        lines.append(
            f"| — | {VARIANT_DISPLAY.get(v, v)} | {s['rouge_l']:.4f} | {delta:+.4f} |"
        )
        prev_rouge = s["rouge_l"]

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  📄 Ablation table → {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="eduRAG result aggregator")
    p.add_argument("--dataset",          required=True)
    p.add_argument("--results-dir",      required=True)
    p.add_argument("--output",           required=True, help="Output aggregate JSON")
    p.add_argument("--emit-markdown",    default=None,  help="Emit markdown summary here")
    p.add_argument("--emit-ablation-table", default=None, help="Emit ablation delta table here")

    args = p.parse_args()

    results = load_results(args.results_dir, args.dataset)
    if not results:
        print(f"⚠️  No JSON files found for dataset='{args.dataset}' in {args.results_dir}")

    summary = aggregate(results)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({"dataset": args.dataset, "variants": summary}, f, indent=2)
    print(f"  ✅ Aggregate JSON → {args.output}")

    if args.emit_markdown:
        emit_markdown(summary, args.dataset, args.emit_markdown)

    if args.emit_ablation_table:
        emit_ablation_table(summary, args.dataset, args.emit_ablation_table)


if __name__ == "__main__":
    main()
