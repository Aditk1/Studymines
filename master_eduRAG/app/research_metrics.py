"""
Research metric aggregation from graph artifacts, database snapshots, and exported evaluations.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import networkx as nx
import numpy as np
from networkx.algorithms.community.quality import modularity
from networkx.readwrite import json_graph

from src.utils.config import load_config


import sys

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).resolve().parent
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent

GRAPH_DIR = ROOT_DIR / "data" / "graphs"
METRICS_PATH = ROOT_DIR / "outputs" / "research" / "metrics.json"
SNAPSHOT_PATH = ROOT_DIR / "outputs" / "research_metrics_snapshot.json"


@dataclass
class GraphArtifactMetrics:
    """Define the GraphArtifactMetrics data structure or service used by this module."""
    artifact: str
    nodes: int
    edges: int
    communities: int
    weighted_modularity: float
    mean_community_coherence: float
    avg_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "nodes": self.nodes,
            "edges": self.edges,
            "communities": self.communities,
            "weighted_modularity": self.weighted_modularity,
            "mean_community_coherence": self.mean_community_coherence,
            "avg_confidence": self.avg_confidence,
        }


def _round(value: float | None, places: int = 4) -> float | None:
    if value is None:
        return None
    return round(float(value), places)


def _safe_mean(values: list[float]) -> float | None:
    return _round(mean(values)) if values else None


def _load_graph_artifact(path: Path) -> tuple[nx.Graph, dict[str, Any]]:
    with path.open("rb") as fh:
        head = fh.read(1)

    if head == b"{":
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        graph_obj = json_graph.node_link_graph(data["graph"])
        stats = data.get("stats", {})
        return graph_obj, stats

    with path.open("rb") as fh:
        data = pickle.load(fh)

    if isinstance(data, dict):
        graph_obj = data.get("graph", data)
        stats = data.get("stats", {})
    else:
        graph_obj = data
        stats = {}

    return graph_obj, stats


def _compute_community_coherence(graph: nx.Graph) -> float:
    scores: list[float] = []
    community_embeddings: dict[int, list[np.ndarray]] = {}

    for node, data in graph.nodes(data=True):
        community_id = data.get("community", -1)
        embedding = data.get("embedding", [])
        if community_id >= 0 and embedding:
            community_embeddings.setdefault(community_id, []).append(np.asarray(embedding, dtype=float))

    for embeddings in community_embeddings.values():
        if len(embeddings) < 2:
            scores.append(1.0)
            continue
        matrix = np.vstack(embeddings)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        matrix = matrix / norms
        sim = matrix @ matrix.T
        upper = sim[np.triu_indices(len(embeddings), k=1)]
        if upper.size:
            scores.append(float(np.mean(upper)))

    return _round(mean(scores) if scores else 0.0) or 0.0


def _compute_graph_metrics(path: Path) -> GraphArtifactMetrics:
    graph, stats = _load_graph_artifact(path)
    undirected = graph.to_undirected()

    community_map: dict[int, set[str]] = {}
    for node, data in graph.nodes(data=True):
        community_id = data.get("community", -1)
        if community_id != -1:
            community_map.setdefault(community_id, set()).add(node)

    communities = list(community_map.values())
    for u, v, edge_data in undirected.edges(data=True):
        edge_data["weight"] = edge_data.get("confidence", 1.0)

    weighted_mod = modularity(undirected, communities, weight="weight") if len(communities) > 1 else 0.0
    confidences = [float(data.get("confidence", 0.0)) for _, _, data in graph.edges(data=True)]

    return GraphArtifactMetrics(
        artifact=path.name,
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
        communities=len(communities),
        weighted_modularity=_round(weighted_mod) or 0.0,
        mean_community_coherence=_compute_community_coherence(graph),
        avg_confidence=_round(stats.get("avg_confidence", np.mean(confidences) if confidences else 0.0)) or 0.0,
    )


def _scan_graph_metrics() -> tuple[list[GraphArtifactMetrics], dict[str, Any]]:
    graph_files = sorted(p for p in GRAPH_DIR.glob("*") if p.is_file())
    reports = [_compute_graph_metrics(path) for path in graph_files]

    aggregate = {
        "graph_artifacts": len(reports),
        "avg_nodes": _safe_mean([float(r.nodes) for r in reports]),
        "avg_edges": _safe_mean([float(r.edges) for r in reports]),
        "avg_communities": _safe_mean([float(r.communities) for r in reports]),
        "avg_weighted_modularity": _safe_mean([r.weighted_modularity for r in reports]),
        "avg_mean_community_coherence": _safe_mean([r.mean_community_coherence for r in reports]),
        "avg_confidence": _safe_mean([r.avg_confidence for r in reports]),
    }
    primary = max(reports, key=lambda item: (item.nodes, item.edges)).to_dict() if reports else None
    return reports, {"aggregate": aggregate, "primary_graph": primary}


def _load_db_snapshot() -> dict[str, Any]:
    from app.database import SessionLocal
    from sqlalchemy import text
    snapshot = {
        "uploads_total": 0,
        "uploads_with_graph": 0,
        "uploads_with_summary": 0,
    }

    db = SessionLocal()
    try:
        snapshot["uploads_total"] = db.execute(text("SELECT COUNT(*) FROM uploads")).scalar() or 0
        snapshot["uploads_with_graph"] = db.execute(text("SELECT COUNT(*) FROM uploads WHERE graph_path IS NOT NULL")).scalar() or 0

        summaries = 0
        for row in db.execute(text("SELECT study_package FROM uploads WHERE study_package IS NOT NULL")).fetchall():
            try:
                payload_str = row[0]
                payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
                data = payload.get("data", payload) if isinstance(payload, dict) else payload
                summary = (data.get("summary") or {}) if isinstance(data, dict) else {}
                if isinstance(summary, dict) and str(summary.get("content", "")).strip():
                    summaries += 1
            except Exception:
                continue
        snapshot["uploads_with_summary"] = summaries
        return snapshot
    except Exception:
        return snapshot
    finally:
        db.close()


def _load_live_config() -> dict[str, Any]:
    config = load_config(ROOT_DIR / "config" / "base.yaml")
    return {
        "llm_provider": config.llm.provider,
        "llm_model": config.llm.model,
        "embedding_model": config.embeddings.model,
        "temperature": config.llm.temperature,
        "chunk_size": config.ingestion.chunk_size,
        "chunk_overlap": config.ingestion.chunk_overlap,
        "context_max_tokens": config.retrieval.context_max_tokens,
        "parallel_enabled": config.parallel.enabled,
        "max_concurrent_entities": config.parallel.max_concurrent_entities,
        "community_strategy": config.community.strategy,
        "traversal_strategy": config.traversal.strategy,
    }


def _build_snapshot_metrics() -> dict[str, Any]:
    reports, graph_summary = _scan_graph_metrics()
    db_snapshot = _load_db_snapshot()

    return {
        "success": True,
        "summary_metrics": {
            "edusum": {
                "rouge1": None,
                "rouge2": None,
                "rougeL": None,
                "bertscore": None,
                "meteor": None,
                "status": "unavailable",
                "note": "No gold reference summaries or exported benchmark logs were found in this repo snapshot.",
            },
            "baselines": {},
        },
        "graph_metrics": {
            "per_artifact": [report.to_dict() for report in reports],
            **graph_summary,
        },
        "vision_metrics": {
            "saeocr": {"wer": None, "cer": None, "accuracy": None},
            "tesseract": {"wer": None, "cer": None, "accuracy": None},
            "status": "unavailable",
            "note": "No labeled OCR benchmark set or exported vision-eval logs were found in this repo snapshot.",
        },
        "educational_utility": {},
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "live_repo_snapshot",
            "db": db_snapshot,
            "system_config": _load_live_config(),
        },
    }


def get_research_metrics() -> dict[str, Any]:
    """Handle the get research metrics operation."""
    if METRICS_PATH.exists():
        with METRICS_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return _build_snapshot_metrics()


def write_research_snapshot() -> Path:
    """Handle the write research snapshot operation."""
    snapshot = _build_snapshot_metrics()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2)
    return SNAPSHOT_PATH
