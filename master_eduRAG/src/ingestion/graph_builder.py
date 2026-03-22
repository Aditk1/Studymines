"""
Graph builder: assembles the KnowledgeGraph from scored triples
and populates node embeddings for vector search.
"""
from __future__ import annotations

from src.graph.knowledge_graph import KnowledgeGraph, Triple
from src.utils.logger import get_logger
from src.utils.vector_store import EmbeddingModel, VectorStore

logger = get_logger("graph_builder")


class GraphBuilder:
    """
    Builds a KnowledgeGraph from triples and populates embeddings.

    Flow:
        triples → add to graph → embed entity labels → store in vector DB
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
    ) -> None:
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def build(self, triples: list[Triple]) -> KnowledgeGraph:
        """
        Construct a KnowledgeGraph from a list of triples.

        Args:
            triples: List of Triple objects (with C(t) confidence scores).

        Returns:
            Populated KnowledgeGraph ready for community detection.
        """
        kg = KnowledgeGraph()
        kg.add_triples(triples)

        # Embed all entity labels and store in vector DB
        entities = kg.get_all_entities()
        if entities:
            self._embed_and_store(entities, kg)

        summary = kg.summary()
        logger.info("graph_built", **summary)
        return kg

    def _embed_and_store(self, entities: list[str], kg: KnowledgeGraph) -> None:
        """Embed entity labels and register them in the vector store."""
        try:
            embeddings = self.embedding_model.encode(entities, normalize=True)
            entity_ids = entities
            entity_labels = entities
            metadata = [
                {"community": str(kg.get_community(e)), "mention_count": str(1)}
                for e in entities
            ]

            # Store embeddings on graph nodes
            for entity, emb in zip(entities, embeddings):
                kg.set_node_embedding(entity, emb.tolist())

            # Store in vector DB for semantic lookup
            self.vector_store.add_entities(
                entity_ids=entity_ids,
                entity_labels=entity_labels,
                embeddings=embeddings.tolist(),
                metadata=metadata,
            )
            logger.info("entities_embedded", count=len(entities))
        except Exception as e:
            logger.error("embedding_failed", error=str(e))

    def update_embeddings_after_community(self, kg: KnowledgeGraph) -> None:
        """
        Refresh vector store metadata after community detection is complete.
        Updates community_id in each entity's metadata.
        """
        entities = kg.get_all_entities()
        if not entities:
            return

        embeddings = self.embedding_model.encode(entities, normalize=True)
        metadata = [
            {"community": str(kg.get_community(e))}
            for e in entities
        ]
        self.vector_store.add_entities(
            entity_ids=entities,
            entity_labels=entities,
            embeddings=embeddings.tolist(),
            metadata=metadata,
        )
        logger.info("embeddings_updated_post_community", count=len(entities))
