#!/usr/bin/env python3
"""
scripts/community_ab.py — Community-detection A/B comparison.

Corresponds to `scripts.community_ab` in run_commands.md §4c.
Runs both Leiden and CW-Leiden on a pre-built graph and compares.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graph.knowledge_graph import KnowledgeGraph
from src.evaluation.metrics import evaluate_graph_quality
from src.utils.error_handler import wrap_explain


def run_ab(args: argparse.Namespace) -> None:
    graph_path = Path(args.graph)
    if not graph_path.exists():
        print(f"❌ Graph not found: {graph_path}")
        sys.exit(1)

    results = {}

    for algo in args.algorithms:
        print(f"  Running community detection: {algo} …")
        # Load a fresh copy for each algorithm to avoid state bleed
        graph = KnowledgeGraph.load(graph_path)

        from src.utils.config import AppConfig, CommunityConfig, CWLeidenConfig, LeidenConfig
        import dataclasses

        # Build a minimal config for the detector
        cc = CommunityConfig(
            strategy=algo,
            leiden=LeidenConfig(resolution=args.resolution, n_iterations=args.iterations, seed=args.seed),
            cw_leiden=CWLeidenConfig(resolution=args.resolution, n_iterations=args.iterations, seed=args.seed),
        )

        from src.community.detectors import build_community_detector
        detector = build_community_detector(cc, llm_client=None)
        info = detector.apply(graph)

        gq = evaluate_graph_quality(graph, algo)
        num_communities = info.get("num_communities", 0)

        results[algo] = {
            "algorithm": algo,
            "num_communities": num_communities,
            "weighted_modularity": round(gq.weighted_modularity, 4),
            "community_coherence": round(gq.community_coherence, 4),
        }
        print(f"     {algo}: communities={num_communities}  Q_w={gq.weighted_modularity:.4f}  coherence={gq.community_coherence:.4f}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  ✅ A/B results → {out_path}")


@wrap_explain(context="Running Community A/B Comparison")
def main() -> None:
    p = argparse.ArgumentParser(description="Community detection A/B comparison")
    p.add_argument("--graph",       required=True, help="Pre-built graph pickle path (.pkl)")
    p.add_argument("--algorithms",  required=True, nargs="+", help="e.g. leiden cw_leiden")
    p.add_argument("--resolution",  type=float, default=1.0)
    p.add_argument("--seed",        type=int,   default=42)
    p.add_argument("--iterations",  type=int,   default=10)
    p.add_argument("--output",      required=True, help="Output JSON path")
    args = p.parse_args()
    run_ab(args)


if __name__ == "__main__":
    main()
