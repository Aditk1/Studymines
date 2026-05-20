"""
ChromaDB vector store wrapper.
Used for entity embedding storage and seed entity lookup.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from src.utils.config import VectorStoreConfig
from src.utils.logger import get_logger

logger = get_logger("vector_store")


@dataclass
class SearchResult:
    """Define the SearchResult data structure or service used by this module."""
    entity_id: str
    entity_label: str
    score: float
    metadata: dict[str, Any]


class VectorStore:
    """
    ChromaDB-backed entity vector store.

    Stores entity embeddings and enables semantic seed entity lookup.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        self.config = config
        self._collection: Any = None
        self._init()

    def _init(self) -> None:
        try:
            import chromadb  # type: ignore
            from chromadb.config import Settings  # type: ignore

            persist_dir = Path(self.config.persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)

            client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric},
            )
            logger.info("vector_store_initialized", collection=self.config.collection_name)
        except ImportError:
            logger.error("chromadb_not_installed", msg="pip install chromadb")
            raise

    def add_entities(
        self,
        entity_ids: list[str],
        entity_labels: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add entities to the vector store."""
        if not entity_ids:
            return
        meta = metadata or [{} for _ in entity_ids]
        # ChromaDB requires string IDs and no None metadata values
        clean_meta = [
            {k: str(v) for k, v in m.items() if v is not None}
            for m in meta
        ]
        self._collection.upsert(
            ids=entity_ids,
            embeddings=embeddings,
            documents=entity_labels,
            metadatas=clean_meta,
        )
        logger.debug("entities_added", count=len(entity_ids))

    def search(self, query_embedding: list[float], top_k: int | None = None) -> list[SearchResult]:
        """
        Find the top-k most similar entities to the query embedding.

        Args:
            query_embedding: Embedding vector of the query.
            top_k: Number of results. Defaults to config value.

        Returns:
            List of SearchResult sorted by relevance.
        """
        k = top_k or self.config.top_k
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self._collection.count() or 1),
            include=["documents", "distances", "metadatas"],
        )

        search_results: list[SearchResult] = []
        ids = results["ids"][0]
        docs = results["documents"][0]
        distances = results["distances"][0]
        metas = results["metadatas"][0]

        for eid, doc, dist, meta in zip(ids, docs, distances, metas):
            # Convert distance to similarity score (cosine: 1 - distance)
            score = float(1.0 - dist) if dist <= 2.0 else 0.0
            search_results.append(
                SearchResult(entity_id=eid, entity_label=doc, score=score, metadata=meta)
            )
        return search_results

    def count(self) -> int:
        """Return total number of stored entities."""
        return self._collection.count()

    def clear(self) -> None:
        """Remove all entities from the collection."""
        self._collection.delete(where={"__dummy__": {"$ne": "x"}})
        logger.info("vector_store_cleared")


class EmbeddingModel:
    """
    Wrapper for sentence-transformers embeddings.
    Handles device selection and batch encoding.
    """

    def __init__(self, model_name: str, device: str = "cuda", batch_size: int = 32) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model: Any = None
        self._device = self._resolve_device(device)

    @staticmethod
    def _resolve_device(device: str) -> str:
        try:
            import torch  # type: ignore
            if device == "cuda" and torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def _load(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(self.model_name, device=self._device)
            logger.info("embedding_model_loaded", model=self.model_name, device=self._device)

    def encode(self, texts: list[str], normalize: bool = True) -> np.ndarray:
        """
        Encode a list of texts to embeddings.

        Args:
            texts: Input strings.
            normalize: Whether to L2-normalize embeddings.

        Returns:
            Numpy array of shape (len(texts), embedding_dim).
        """
        self._load()
        embeddings = self._model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return np.array(embeddings)

    def encode_single(self, text: str, normalize: bool = True) -> list[float]:
        """Encode a single text and return as list."""
        return self.encode([text], normalize).tolist()[0]
