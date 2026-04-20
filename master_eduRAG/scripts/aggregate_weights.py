#!/usr/bin/env python3
"""
scripts/aggregate_weights.py — Aggregate weight-sensitivity run JSONs.

Corresponds to `scripts.aggregate_weights` in run_commands.md §5.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

CFG_META = {
    "weights_baseline":  {"factuality": 0.40, "specificity": 0.35, "coherence": 0.25, "label": "Baseline"},
    "weights_variant_a": {"factuality": 0.50, "specificity": 0.30, "coherence": 0.20, "label": "Variant A"},
    "weights_variant_b": {"factuality": 0.40, "specificity": 0.40, "coherence": 0.20, "label": "Variant B"},
    "weights_variant_c": {"factuality": 0.30, "specificity": 0.35, "coherence": 0.35, "label": "Variant C"},
    "weights_variant_d": {"factuality": 0.33, "specificity": 0.33, "coherence": 0.34, "label": "Variant D (equal)"},
}


def main() -> None:
    p = argparse.ArgumentParser(description="Aggregate weight-sensitivity results")
    p.add_argument("--inputs",         required=True, help="Glob pattern, e.g. 'results/raw_results/weights_*.json'")
    p.add_argument("--output",         default=None,  help="Output aggregate JSON (optional)")
    p.add_argument("--emit-markdown",  required=True, help="Emit markdown sensitivity table here")
    args = p.parse_args()

    files = sorted(glob.glob(args.inputs))
    rows = []
    for fp in files:
        stem = Path(fp).stem   # e.g. "weights_baseline"
        meta = CFG_META.get(stem, {"factuality": "?", "specificity": "?", "coherence": "?", "label": stem})
        with open(fp) as f:
            data = json.load(f)
        s = data.get("summary", data)
        rows.append({
            "config":       stem,
            "label":        meta["label"],
            "factuality":   meta["factuality"],
            "specificity":  meta["specificity"],
            "coherence":    meta["coherence"],
            "n":            s.get("n_queries", 0),
            "rouge_l":      s.get("rouge_l", 0.0),
            "exact_match":  s.get("exact_match", 0.0),
        })

    if not rows:
        print(f"⚠️  No files matched: {args.inputs}")

    # Markdown table
    lines = [
        "# Confidence Weight Sensitivity Analysis",
        "",
        "| Config | Factuality | Specificity | Coherence | ROUGE-L | Exact Match |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['factuality']} | {r['specificity']} | {r['coherence']}"
            f" | {r['rouge_l']:.4f} | {r['exact_match']:.4f} |"
        )

    Path(args.emit_markdown).parent.mkdir(parents=True, exist_ok=True)
    with open(args.emit_markdown, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  📄 Sensitivity table → {args.emit_markdown}")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(rows, f, indent=2)
        print(f"  ✅ Aggregate JSON → {args.output}")


if __name__ == "__main__":
    main()
