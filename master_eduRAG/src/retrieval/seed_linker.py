"""
Seed Entity Linker.
Maps query text to seed entities in the knowledge graph
using vector similarity search over entity embeddings.
"""
from __future__ import annotations

from src.utils.config import RetrievalConfig
from src.utils.logger import get_logger
from src.utils.vector_store import EmbeddingModel, SearchResult, VectorStore

logger = get_logger("seed_linker")


class SeedEntityLinker:
    """
    Links a natural-language query to seed entities in the graph
    by embedding the query and retrieving the nearest entity vectors.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
        config: RetrievalConfig,
    ) -> None:
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.config = config

    def link(self, query: str) -> list[str]:
        """
        Find the most relevant seed entities for a query.

        Args:
            query: User query string.

        Returns:
            List of entity IDs (strings) sorted by relevance.
        """
        if self.vector_store.count() == 0:
            logger.warning("vector_store_empty")
            return []

        query_embedding = self.embedding_model.encode_single(query, normalize=True)
        results: list[SearchResult] = self.vector_store.search(
            query_embedding, top_k=self.config.seed_entity_top_k
        )

        entities = [r.entity_id for r in results if r.score > 0.1]
        logger.debug("seed_entities_linked", query=query[:60], entities=entities)
        return entities
