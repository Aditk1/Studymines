#!/usr/bin/env python3
"""
scripts/run_experiment.py  — Single-variant experiment runner.

Corresponds to `scripts.run_experiment` in run_commands.md §1–§5.
Wraps src/pipeline.py with a CLI that adds:
  --bucket-by-hops
  --multi-entity-only / --multi-entity-tag
  --log-operational-metrics
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

# ── ensure repo root is on sys.path regardless of invocation style ──
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pipeline import Pipeline
from src.graph.knowledge_graph import KnowledgeGraph
from src.utils.config import load_config, load_config_for_variant


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VARIANT_ALIAS: dict[str, str] = {
    "naive_rag":          "baseline_naive_rag",
    "standard_graphrag":  "baseline_graphrag",
    "plus_c1":            "ablation_c1_only",
    "plus_c1_c2":         "ablation_c1_c2",
    "plus_c1_c2_c3":      "ablation_c1_c2_c3",
    "full_edurag":        "full_system",
}


def _load_qa_pairs(dataset: str, limit: int, seed: int) -> list[dict]:
    """Load (question, gold_answer, hop_count, num_entities) records."""
    rng = random.Random(seed)

    # ── Custom QA: build from existing graph artifacts ──
    if dataset == "custom_qa":
        # Placeholder questions drawn from the paper's custom educational domain
        questions = [
            {
                "id": "cqa_001",
                "question": "What is the relationship between backpropagation and gradient descent?",
                "gold": "Backpropagation computes gradients of the loss with respect to weights, which gradient descent uses to update the parameters iteratively to minimize the loss.",
                "hops": 2,
                "entities": ["backpropagation", "gradient descent"],
            },
            {
                "id": "cqa_002",
                "question": "How does the attention mechanism in Transformers differ from RNN hidden states?",
                "gold": "Attention directly weights all input positions simultaneously, whereas RNN hidden states are sequential and suffer from vanishing gradients over long sequences.",
                "hops": 2,
                "entities": ["attention mechanism", "transformers", "RNN"],
            },
            {
                "id": "cqa_003",
                "question": "What role does the confidence threshold play in the eduRAG graph construction?",
                "gold": "The confidence threshold (default 0.15) filters low-quality triples extracted from text before they are added to the knowledge graph, improving graph precision.",
                "hops": 1,
                "entities": ["confidence threshold", "eduRAG"],
            },
            {
                "id": "cqa_004",
                "question": "How does CW-Leiden differ from standard Leiden community detection?",
                "gold": "CW-Leiden (Confidence-Weighted Leiden) uses triple confidence scores as edge weights in the modularity optimisation, producing communities with higher semantic coherence.",
                "hops": 2,
                "entities": ["CW-Leiden", "Leiden"],
            },
            {
                "id": "cqa_005",
                "question": "What is the purpose of the RLM traverser in multi-hop QA?",
                "gold": "The RLM traverser uses an LLM to decide which graph edges to follow at each step, dynamically adapting traversal depth to the complexity of the question.",
                "hops": 3,
                "entities": ["RLM traverser", "multi-hop QA"],
            },
            {
                "id": "cqa_006",
                "question": "What is CSS specificity?",
                "gold": "CSS specificity is the weight given to a CSS selector that determines which rule is applied when multiple rules match the same element.",
                "hops": 1,
                "entities": ["CSS specificity"],
            },
            {
                "id": "cqa_007",
                "question": "How do HTML semantic elements improve accessibility?",
                "gold": "Semantic elements like <article>, <nav>, and <section> convey meaning to assistive technologies, allowing screen readers to navigate the page structure correctly.",
                "hops": 2,
                "entities": ["HTML semantic elements", "accessibility"],
            },
            {
                "id": "cqa_008",
                "question": "What is the box model in CSS and how does padding differ from margin?",
                "gold": "The CSS box model defines content, padding, border, and margin layers. Padding is inside the border (between content and border); margin is outside (between border and adjacent elements).",
                "hops": 2,
                "entities": ["box model", "padding", "margin"],
            },
        ]
        # Shuffle deterministically and apply limit
        rng.shuffle(questions)
        return questions[:limit] if limit else questions

    # ── MuSiQue / 2Wiki: try to load from data dir, else warn ──
    data_paths = {
        "musique": REPO_ROOT / "data" / "musique" / "data" / "musique_ans.json",
        "2wiki":   REPO_ROOT / "data" / "2WikiMultiHopQA" / "data" / "dev_ids.json",
    }
    path = data_paths.get(dataset)
    if path and path.exists():
        with open(path) as f:
            raw = json.load(f)
        records = []
        for item in raw:
            records.append({
                "id":       item.get("id", ""),
                "question": item.get("question", item.get("input", "")),
                "gold":     item.get("answer", item.get("answers", [""])[0] if isinstance(item.get("answers"), list) else ""),
                "hops":     item.get("num_hops", item.get("type", 2) if isinstance(item.get("type"), int) else 2),
                "entities": item.get("entities", []),
            })
        rng.shuffle(records)
        return records[:limit] if limit else records

    print(f"⚠️  Dataset '{dataset}' not found. See run_commands.md §2/§3 for download instructions.")
    return []


def _compute_percentiles(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    s = sorted(values)
    idx_p50 = int(len(s) * 0.50)
    idx_p95 = int(len(s) * 0.95)
    return s[min(idx_p50, len(s) - 1)], s[min(idx_p95, len(s) - 1)]


# ---------------------------------------------------------------------------
# Core async runner
# ---------------------------------------------------------------------------

async def run_experiment(args: argparse.Namespace) -> dict:
    t_total_start = time.perf_counter()

    # 1. Load config
    variant_key = VARIANT_ALIAS.get(args.variant, args.variant)
    # Derive config_dir from the supplied --config path (e.g. config/sanity.yaml → config/)
    config_path  = Path(args.config)
    config_dir   = config_path.parent if config_path.is_file() else config_path
    try:
        config = load_config_for_variant(variant_key, config_dir=config_dir)
    except FileNotFoundError:
        # Variant YAML absent — fall back to running with just the base/sanity config
        config = load_config(base_path=args.config)
    config.variant_name = args.variant

    # 2. Build pipeline
    pipeline = Pipeline.from_config(config)

    # 3. Load or build graph
    graph_path = Path(args.graph) if args.graph else None
    if graph_path and graph_path.exists():
        print(f"  [LOAD] Loading cached graph from {graph_path}")
        graph = KnowledgeGraph.load(graph_path)
        ingest_result = None
    else:
        print("  [BUILD] Running ingestion (no cached graph provided)...")
        # Load documents from the custom_qa uploads or a minimal set
        docs_dir = REPO_ROOT / "data" / "uploads"
        documents: list[tuple[str, str]] = []
        if docs_dir.exists():
            from src.ingestion.loader import DocumentLoader
            loader = DocumentLoader()
            for p in sorted(docs_dir.iterdir())[:5]:  # limit files for sanity
                try:
                    text = loader.load_file(p)
                    if text:
                        print(f"  + Loaded {p.name}")
                        documents.append((text, p.name))
                except Exception as exc:
                    print(f"  ! Skip {p.name}: {exc}")
        if not documents:
            documents = [("The eduRAG system combines confidence-weighted knowledge graphs with RLM traversal for multi-hop educational QA.", "synthetic_doc")]

        ingest_result = await pipeline.ingest(documents)
        graph = ingest_result.graph
        if graph_path:
            graph_path.parent.mkdir(parents=True, exist_ok=True)
            graph.save(graph_path)
            print(f"  [OK] Graph saved to {graph_path}")

    # 4. Load QA pairs
    qa_pairs = _load_qa_pairs(args.dataset, args.limit, args.seed)
    if not qa_pairs:
        return {"error": f"No QA pairs loaded for dataset={args.dataset}"}

    # 5. Run queries
    results = []
    latencies_ms: list[float] = []
    tokens_per_query: list[int] = []
    nodes_per_query: list[int] = []

    print(f"  [RUN] Running {len(qa_pairs)} queries [{args.variant}] ...")
    for i, qa in enumerate(qa_pairs, 1):
        # Multi-entity-only filter
        if args.multi_entity_only or args.multi_entity_tag:
            if len(qa.get("entities", [])) < 2:
                continue

        qr = await pipeline.query(
            question=qa["question"],
            graph=graph,
            query_id=qa["id"],
            gold_answer=qa["gold"],
            dataset=args.dataset,
        )
        lat_ms = qr.latency_seconds * 1000
        tok = (qr.prompt_tokens or 0) + (qr.completion_tokens or 0)
        latencies_ms.append(lat_ms)
        tokens_per_query.append(tok)
        nodes_per_query.append(qr.nodes_visited or 0)

        rec = qr.to_dict()
        rec["hop_count"] = qa.get("hops", 1)
        rec["num_entities"] = len(qa.get("entities", []))
        results.append(rec)

        print(f"     [{i}/{len(qa_pairs)}] ROUGE-L={qr.rouge_l:.3f}  EM={qr.exact_match}  lat={lat_ms:.0f}ms")

    if not results:
        return {"error": "No results after filtering"}

    # 6. Aggregate
    rouge_vals = [r["rouge_l"] for r in results]
    f1_vals    = [r["token_f1"] for r in results]
    em_vals    = [r["exact_match"] for r in results]

    p50_lat, p95_lat = _compute_percentiles(latencies_ms)
    summary: dict = {
        "variant":    args.variant,
        "dataset":    args.dataset,
        "n_queries":  len(results),
        "rouge_l":    round(sum(rouge_vals) / len(rouge_vals), 4) if rouge_vals else 0.0,
        "token_f1":   round(sum(f1_vals)    / len(f1_vals),    4) if f1_vals    else 0.0,
        "exact_match":round(sum(em_vals)    / len(em_vals),    4) if em_vals    else 0.0,
    }

    if args.log_operational_metrics:
        summary["operational"] = {
            "avg_latency_ms":    round(sum(latencies_ms) / len(latencies_ms), 1) if latencies_ms else 0,
            "p50_latency_ms":    round(p50_lat, 1),
            "p95_latency_ms":    round(p95_lat, 1),
            "avg_tokens":        round(sum(tokens_per_query) / len(tokens_per_query), 1) if tokens_per_query else 0,
            "avg_nodes_visited": round(sum(nodes_per_query)  / len(nodes_per_query),  1) if nodes_per_query  else 0,
            "total_wall_s":      round(time.perf_counter() - t_total_start, 2),
        }

    if args.bucket_by_hops:
        hop_buckets: dict[int, list[float]] = defaultdict(list)
        for r in results:
            hop_buckets[r.get("hop_count", 1)].append(r["rouge_l"])
        summary["hop_breakdown"] = {
            str(h): round(sum(v) / len(v), 4) for h, v in sorted(hop_buckets.items())
        }

    output = {
        "summary": summary,
        "per_query": results,
    }

    # 7. Write output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  [OK] Results written -> {out_path}")
    print(f"  ROUGE-L: {summary['rouge_l']:.4f}  EM: {summary['exact_match']:.4f}")

    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="eduRAG single-variant experiment runner")
    p.add_argument("--config",   required=True,  help="Path to base YAML config")
    p.add_argument("--dataset",  required=True,  help="Dataset name: custom_qa | musique | 2wiki")
    p.add_argument("--variant",  required=True,  help="Variant name: full_edurag | naive_rag | …")
    p.add_argument("--output",   required=True,  help="Output JSON path")
    p.add_argument("--graph",    default=None,   help="Optional pre-built graph pickle (.pkl) path")
    p.add_argument("--limit",    type=int, default=0, help="Max questions (0 = all)")
    p.add_argument("--seed",     type=int, default=42)

    # Optional instrumentation flags (all absent in original codebase)
    p.add_argument("--bucket-by-hops",          action="store_true",
                   help="Break results down by hop complexity")
    p.add_argument("--multi-entity-only",        action="store_true",
                   help="Evaluate only multi-entity questions (≥2 seeds)")
    p.add_argument("--multi-entity-tag",         action="store_true",
                   help="Alias of --multi-entity-only (blueprint §4 name)")
    p.add_argument("--log-operational-metrics",  action="store_true",
                   help="Emit latency / token / node-visit stats in output JSON")

    args = p.parse_args()
    asyncio.run(run_experiment(args))


if __name__ == "__main__":
    main()
