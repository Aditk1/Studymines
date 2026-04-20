#!/usr/bin/env python3
"""
scripts/build_graph.py — Graph construction CLI.

Corresponds to `scripts.build_graph` in run_commands.md §2b, §3b, §4a.
Wraps src/pipeline.ingest() with flags:
  --confidence-on
  --dump-confidence-histogram
  --dump-per-method-stats
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pipeline import Pipeline
from src.utils.config import load_config


async def build_graph(args: argparse.Namespace) -> None:
    config = load_config(base_path=args.config)
    config.variant_name = "build_graph"

    if args.confidence_on:
        config.confidence.enabled = True

    pipeline = Pipeline.from_config(config)

    # ── Load documents ──
    input_path = Path(args.input)
    documents: list[tuple[str, str]] = []

    from src.ingestion.loader import DocumentLoader
    loader = DocumentLoader()

    if input_path.is_dir():
        for p in sorted(input_path.iterdir()):
            if p.suffix.lower() in {".pdf", ".docx", ".txt", ".md", ".jsonl", ".json"}:
                try:
                    text = loader.load_file(p)
                    if text:
                        documents.append((text, p.name))
                        print(f"  ✓ Loaded {p.name}")
                except Exception as exc:
                    print(f"  ⚠  Skip {p.name}: {exc}")
    elif input_path.exists():
        try:
            text = loader.load_file(input_path)
            if text:
                documents.append((text, input_path.name))
        except Exception as exc:
            print(f"  ⚠  Could not load {input_path}: {exc}")
    else:
        print(f"❌ Input not found: {input_path}")
        sys.exit(1)

    if not documents:
        print("❌ No documents loaded. Aborting.")
        sys.exit(1)

    print(f"  Loaded {len(documents)} document(s). Running ingestion …")

    # ── Run ingestion ──
    save_path = Path(args.output)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    ingest_result = await pipeline.ingest(documents, save_path=save_path)

    print(f"  ✅ Graph saved → {save_path}")
    print(f"     Nodes: {ingest_result.graph.num_nodes}  Edges: {ingest_result.graph.num_edges}")
    print(f"     Triples raw: {ingest_result.num_triples_raw}  Kept: {ingest_result.num_triples_kept}")
    if ingest_result.graph_quality:
        gq = ingest_result.graph_quality
        print(f"     Modularity: {gq.weighted_modularity:.4f}  Coherence: {gq.community_coherence:.4f}")

    # ── Optional dumps ──
    if args.dump_confidence_histogram:
        _write_confidence_histogram(ingest_result, args.dump_confidence_histogram)

    if args.dump_per_method_stats:
        _write_per_method_stats(ingest_result, args.dump_per_method_stats)

    # ── Optional log ──
    if args.log:
        log_path = Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            import json as _json
            f.write(_json.dumps({
                "source": str(input_path),
                "output": str(save_path),
                "nodes": ingest_result.graph.num_nodes,
                "edges": ingest_result.graph.num_edges,
                "triples_raw": ingest_result.num_triples_raw,
                "triples_kept": ingest_result.num_triples_kept,
            }) + "\n")


def _write_confidence_histogram(ingest_result, out_path: str) -> None:
    """Emit confidence-bucket histogram from the graph edge weights."""
    graph = ingest_result.graph
    buckets = {
        "0.00-0.15": 0,
        "0.15-0.30": 0,
        "0.30-0.50": 0,
        "0.50-0.70": 0,
        "0.70-1.00": 0,
    }
    confidences: list[float] = []
    for _, _, data in graph._graph.edges(data=True):
        c = data.get("confidence", 0.0)
        confidences.append(c)
        if   c < 0.15: buckets["0.00-0.15"] += 1
        elif c < 0.30: buckets["0.15-0.30"] += 1
        elif c < 0.50: buckets["0.30-0.50"] += 1
        elif c < 0.70: buckets["0.50-0.70"] += 1
        else:           buckets["0.70-1.00"] += 1

    total = len(confidences)
    hist = {
        "total_triples": total,
        "mean_confidence": round(sum(confidences) / total, 4) if total else 0.0,
        "buckets": {k: {"count": v, "pct": round(v / total * 100, 1) if total else 0} for k, v in buckets.items()},
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        import json as _json
        _json.dump(hist, f, indent=2)
    print(f"  📊 Confidence histogram → {out_path}")


def _write_per_method_stats(ingest_result, out_path: str) -> None:
    """Emit per-extraction-method triple counts (placeholder from graph metadata)."""
    graph = ingest_result.graph
    method_counts: dict[str, list[float]] = defaultdict(list)
    for _, _, data in graph._graph.edges(data=True):
        method = data.get("extraction_method", "unknown")
        conf   = data.get("confidence", 0.0)
        method_counts[method].append(conf)

    stats = {}
    for method, confs in method_counts.items():
        stats[method] = {
            "triple_count": len(confs),
            "avg_confidence": round(sum(confs) / len(confs), 4) if confs else 0.0,
        }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        import json as _json
        _json.dump(stats, f, indent=2)
    print(f"  📊 Per-method stats → {out_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="eduRAG graph construction CLI")
    p.add_argument("--config",                   required=True,  help="Base YAML config path")
    p.add_argument("--input",                    required=True,  help="Input: file or directory of documents")
    p.add_argument("--output",                   required=True,  help="Output graph pickle path (.pkl)")
    p.add_argument("--confidence-on",            action="store_true", help="Force confidence.enabled=True")
    p.add_argument("--dump-confidence-histogram",default=None,   help="Write confidence histogram JSON here")
    p.add_argument("--dump-per-method-stats",    default=None,   help="Write per-method triple stats JSON here")
    p.add_argument("--log",                      default=None,   help="Append build summary to this log file")

    args = p.parse_args()
    asyncio.run(build_graph(args))


if __name__ == "__main__":
    main()
