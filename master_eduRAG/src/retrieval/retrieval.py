"""
Retrieval module: seed entity linking and context assembly.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any

from src.utils.config import RetrievalConfig
from src.utils.logger import get_logger
from src.utils.vector_store import EmbeddingModel, VectorStore
from src.graph.knowledge_graph import KnowledgeGraph
from src.traversal.base import TraversalResult

logger = get_logger("retrieval")


class SeedEntityLinker:
    """Links query text to seed entities in the KG via vector similarity."""

    def __init__(self, embedding_model: EmbeddingModel, vector_store: VectorStore, config: RetrievalConfig) -> None:
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.config = config

    def find_seeds(self, query: str, graph: KnowledgeGraph) -> list[str]:
        seeds: list[str] = []
        try:
            query_emb = self.embedding_model.encode_single(query, normalize=True)
            results = self.vector_store.search(query_emb, top_k=self.config.seed_entity_top_k)
            for r in results:
                entity = r.entity_id.lower()
                if graph.entity_exists(entity):
                    seeds.append(entity)
        except Exception as e:
            logger.warning("seed_vector_search_failed", error=str(e))

        query_lower = query.lower()
        for entity in graph.get_all_entities():
            if entity in query_lower and entity not in seeds:
                seeds.append(entity)

        seeds = list(dict.fromkeys(seeds))
        logger.debug("seeds_found", query=query[:80], seeds=seeds[:5])
        return seeds[: self.config.seed_entity_top_k]


class ContextAssembler:
    """Assembles deduplicated context string from traversal results."""

    def __init__(self, config: RetrievalConfig) -> None:
        self.config = config

    def assemble(self, result: TraversalResult, graph: KnowledgeGraph | None = None) -> str:
        triples = sorted(result.retrieved_triples, key=lambda t: t.confidence, reverse=True)
        lines: list[str] = []
        seen: set[str] = set()
        tokens = 0

        for triple in triples:
            if tokens >= self.config.context_max_tokens:
                break
            text = f"({triple.subject}, {triple.relation}, {triple.obj})"
            if text in seen:
                continue
            if self._near_dup(text, seen):
                continue
            seen.add(text)
            lines.append(text)
            tokens += len(text.split())

        return "\n".join(lines)

    def _near_dup(self, text: str, seen: set[str]) -> bool:
        tokens = set(text.lower().split())
        for s in list(seen)[-20:]:
            st = set(s.lower().split())
            if tokens and st:
                overlap = len(tokens & st) / len(tokens | st)
                if overlap >= self.config.dedup_similarity_threshold:
                    return True
        return False
