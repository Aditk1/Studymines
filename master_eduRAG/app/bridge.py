"""
RAG Bridge — The central integration point between Studymines and RLM-GraphRAG.

This module:
1. Takes text extracted by Studymines parsers/vision and feeds it into the
   RLM-GraphRAG ingestion pipeline (Triple Extraction → Confidence Scoring →
   Graph Construction → Community Detection).
2. Enriches Studymines study packages with graph metadata and confidence labels.
3. Provides a query interface for multi-hop reasoning over the Knowledge Graph.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.utils import get_logger

logger = get_logger(__name__)

# Ensure the rag_engine package is importable
PROJECT_ROOT = Path(__file__).parent.parent
RAG_PATH = PROJECT_ROOT / "src"
if str(RAG_PATH) not in sys.path:
    sys.path.insert(0, str(RAG_PATH))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.pipeline import Pipeline, IngestResult
    from app.utils import load_config
    RAG_AVAILABLE = True
except ImportError as _import_err:
    RAG_AVAILABLE = False
    logger.warning(f"RLM-GraphRAG engine not loaded ({_import_err}). Graph features disabled.")


class RAGBridge:
    """
    Bridges the gap between basic summarisation and graph-based reasoning.

    Lifecycle:
        bridge = RAGBridge()
        stats  = bridge.ingest_to_graph(extracted_text, "lecture_01.pdf")
        pkg    = bridge.enrich_study_package(study_package, stats)
        answer = bridge.query_graph("What is backpropagation?", stats["graph_path"])
    """

    def __init__(self, variant: str = "full_system"):
        self.pipeline: Optional[Pipeline] = None
        self._last_graph = None

        if not RAG_AVAILABLE:
            return

        from app.utils import get_config_path
        config_path = get_config_path("base.yaml")
        if not config_path.exists():
            logger.warning(f"Config not found at {config_path}")
            return

        try:
            config = load_config(str(config_path))
            config.variant_name = variant
            self.pipeline = Pipeline.from_config(config)
        except Exception as exc:
            logger.error(f"Could not initialise RAG pipeline: {exc}")

    # ── Ingestion ─────────────────────────────────────────────────────────

    async def ingest_to_graph(
        self,
        text: str,
        source_name: str,
        save_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Feed extracted text into the RLM-GraphRAG pipeline.
        """
        if not self.pipeline:
            return {"success": False, "error": "RAG Pipeline not initialised"}

        documents = [(text, source_name)]
        if not save_dir:
            save_dir = str(PROJECT_ROOT / "data" / "graphs")
        os.makedirs(save_dir, exist_ok=True)

        graph_filename = f"graph_{os.path.splitext(source_name)[0]}.pkl"
        save_path = os.path.join(save_dir, graph_filename)

        try:
            result: IngestResult = await self.pipeline.ingest(documents, save_path=save_path)
            logger.info(f"Ingestion successful. Triples: {result.num_triples_kept}")
            self._last_graph = result.graph

            return {
                "success": True,
                "num_triples": result.num_triples_kept,
                "confidence_ratio": (
                    result.num_triples_kept / result.num_triples_raw
                    if result.num_triples_raw > 0
                    else 0
                ),
                "graph_path": save_path,
                "num_communities": (
                    len(result.graph.communities)
                    if hasattr(result.graph, "communities")
                    else 0
                ),
                "nodes": result.graph.get_all_entities()
            }
        except Exception as exc:
            logger.error(f"Ingestion error: {exc}")
            return {"success": False, "error": str(exc)}

    # ── Enrichment ────────────────────────────────────────────────────────

    def enrich_study_package(
        self,
        study_package: Dict[str, Any],
        graph_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Inject graph metadata and confidence labels into a Studymines
        study package.  (Milestone 2 — Confidence-Aware Study Cards)
        """
        if not graph_stats.get("success"):
            return study_package

        conf_ratio = graph_stats.get("confidence_ratio", 0)
        study_package["graph_metadata"] = {
            "triples_count": graph_stats.get("num_triples"),
            "extraction_confidence": round(conf_ratio * 100, 2),
            "graph_status": "verified" if conf_ratio > 0.6 else "review_required",
            "communities_count": graph_stats.get("num_communities"),
            "graph_path": graph_stats.get("graph_path"),
        }

        label = "Verified" if conf_ratio > 0.5 else "Needs Review"

        if "data" in study_package:
            for concept in study_package["data"].get("concepts", []):
                concept["verification_status"] = label
                concept["graph_node_id"] = concept.get("name", "").lower().replace(" ", "_")

            for card in study_package["data"].get("flashcards", []):
                card["is_graph_grounded"] = label == "Verified"
                tags = card.get("tags", [])
                tags.append(f"Confidence: {label}")
                card["tags"] = tags

        return study_package

    # ── Query ─────────────────────────────────────────────────────────────

    async def query_graph(
        self,
        question: str,
        graph_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Multi-hop question answering over the Knowledge Graph.
        Uses the RLM Traverser (C3) + Parallel Dispatcher (C4).
        """
        if not self.pipeline:
            return {"success": False, "error": "RAG Pipeline not initialised"}

        # Load graph from disk if not cached
        graph = self._last_graph
        if graph is None and graph_path:
            from src.graph.knowledge_graph import KnowledgeGraph
            graph = KnowledgeGraph.load(graph_path)

        if graph is None:
            return {"success": False, "error": "No graph available. Ingest a document first."}

        try:
            result = await self.pipeline.query(question, graph)
            return {
                "success": True,
                "answer": result.predicted_answer,
                "nodes_visited": result.nodes_visited,
                "traversal_depth": result.traversal_depth,
                "strategy": result.strategy,
                "latency_seconds": round(result.latency_seconds, 3),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}


# ── Convenience helpers ───────────────────────────────────────────────────

async def process_with_rag(
    text: str,
    source_name: str,
    study_package: Dict[str, Any],
) -> (Dict[str, Any], Dict[str, Any]):
    """One-call helper: ingest + enrich. Returns (package, stats)"""
    bridge = RAGBridge()
    stats = await bridge.ingest_to_graph(text, source_name)
    pkg = bridge.enrich_study_package(study_package, stats)
    return pkg, stats
