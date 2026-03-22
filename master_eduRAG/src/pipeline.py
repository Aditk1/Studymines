"""
Pipeline: wires all components together into a single callable pipeline.
One Pipeline instance = one experimental variant.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.community.detectors import build_community_detector
from src.evaluation.metrics import (
    GraphQualityReport,
    QueryResult,
    evaluate_answer,
    evaluate_graph_quality,
)
from src.graph.knowledge_graph import KnowledgeGraph
from src.ingestion.confidence import ConfidenceScorer
from src.ingestion.extractor import TripleExtractor
from src.ingestion.graph_builder import GraphBuilder
from src.ingestion.loader import Chunker, DocumentLoader
from src.retrieval.answer_generator import AnswerGenerator, GeneratedAnswer
from src.retrieval.retrieval import ContextAssembler, SeedEntityLinker
from src.traversal.base import FixedHopTraverser, Traverser
from src.traversal.parallel_dispatcher import ParallelDispatcher
from src.traversal.rlm_traverser import RLMTraverser
from src.utils.config import AppConfig
from src.utils.llm_client import LLMClient
from src.utils.logger import get_logger
from src.utils.vector_store import EmbeddingModel, VectorStore

logger = get_logger("pipeline")


@dataclass
class IngestResult:
    graph: KnowledgeGraph
    num_documents: int
    num_chunks: int
    num_triples_raw: int
    num_triples_kept: int
    graph_quality: GraphQualityReport | None


class Pipeline:
    """
    Full RLM-GraphRAG pipeline for one experimental variant.

    Usage:
        pipeline = Pipeline.from_config(config)
        ingest_result = pipeline.ingest(documents)
        result = pipeline.query("What is backpropagation?", ingest_result.graph)
    """

    def __init__(
        self,
        config: AppConfig,
        llm: LLMClient,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
    ) -> None:
        self.config = config
        self.llm = llm
        self.embedding_model = embedding_model
        self.vector_store = vector_store

        self.loader = DocumentLoader()
        self.chunker = Chunker(
            chunk_size=config.ingestion.chunk_size,
            chunk_overlap=config.ingestion.chunk_overlap,
        )
        self.extractor = TripleExtractor(config.ingestion)
        self.confidence_scorer = ConfidenceScorer(config.confidence, llm)
        self.graph_builder = GraphBuilder(embedding_model, vector_store)
        self.community_detector = build_community_detector(config.community, llm_client=llm)
        self.traverser: Traverser = self._build_traverser()
        self.seed_linker = SeedEntityLinker(embedding_model, vector_store, config.retrieval)
        self.context_assembler = ContextAssembler(config.retrieval)
        self.answer_generator = AnswerGenerator(config.answer_generation, llm)

    def _build_traverser(self) -> Traverser:
        strategy = self.config.traversal.strategy
        if strategy == "fixed_hop":
            base: Traverser = FixedHopTraverser(
                k=self.config.traversal.fixed_hop.k,
                min_confidence=self.config.confidence.min_confidence_threshold,
            )
        elif strategy == "rlm":
            base = RLMTraverser(self.config.traversal, self.llm)
        else:
            raise ValueError(f"Unknown traversal strategy: {strategy}")

        if self.config.parallel.enabled:
            return ParallelDispatcher(self.config.parallel, base)
        return base

    @classmethod
    def from_config(cls, config: AppConfig) -> "Pipeline":
        """Construct pipeline from AppConfig. Preferred factory method."""
        llm = LLMClient(config.llm)
        embedding_model = EmbeddingModel(
            model_name=config.embeddings.model,
            device=config.embeddings.device,
            batch_size=config.embeddings.batch_size,
        )
        vs_config = config.vector_store
        # Namespace collection per variant to avoid cross-variant contamination
        vs_config.collection_name = f"entities_{config.variant_name}"
        vector_store = VectorStore(vs_config)
        return cls(config, llm, embedding_model, vector_store)

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def ingest(
        self,
        documents: list[tuple[str, str]],
        save_path: str | Path | None = None,
    ) -> IngestResult:
        """
        Full ingestion pipeline: (text, source) pairs → KG with communities.

        Args:
            documents: List of (text, source_name) tuples.
            save_path: Optional path to persist the graph.

        Returns:
            IngestResult with graph and build statistics.
        """
        logger.info("ingestion_start", variant=self.config.variant_name, num_docs=len(documents))

        # 1. Chunk documents
        all_chunks = self.chunker.chunk_documents(documents)
        logger.info("chunking_done", num_chunks=len(all_chunks))

        # 2. Extract triples
        raw_triples = await self.extractor.extract_from_chunks(all_chunks)
        logger.info("extraction_done", num_raw_triples=len(raw_triples))

        # 3. Confidence scoring (C1)
        context_map = {c.source: c.text for c in all_chunks}
        if self.config.confidence.enabled:
            scored_triples = await self.confidence_scorer.score_batch(raw_triples, context_map)
        else:
            scored_triples = raw_triples
        logger.info("scoring_done", kept=len(scored_triples), discarded=len(raw_triples) - len(scored_triples))

        # 4. Build weighted graph
        graph = self.graph_builder.build(scored_triples)

        # 5. Community detection (C2)
        community_info = self.community_detector.apply(graph)
        logger.info("community_done", num_communities=community_info.get("num_communities", 0))

        # 6. Refresh embeddings with community metadata
        self.graph_builder.update_embeddings_after_community(graph)

        # 7. Evaluate graph quality
        gq = evaluate_graph_quality(graph, self.community_detector.get_name())

        if save_path:
            graph.save(save_path)

        return IngestResult(
            graph=graph,
            num_documents=len(documents),
            num_chunks=len(all_chunks),
            num_triples_raw=len(raw_triples),
            num_triples_kept=len(scored_triples),
            graph_quality=gq,
        )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def query(
        self,
        question: str,
        graph: KnowledgeGraph,
        query_id: str = "",
        gold_answer: str = "",
        dataset: str = "",
    ) -> QueryResult:
        """
        Full query pipeline: question → grounded answer with evaluation metrics.

        Args:
            question: User's natural language question.
            graph: The ingested KnowledgeGraph.
            query_id: Optional identifier for checkpointing.
            gold_answer: Ground truth for evaluation (empty = no eval).
            dataset: Dataset name for result logging.

        Returns:
            QueryResult with predicted answer and all evaluation metrics.
        """
        t_start = time.perf_counter()

        # 1. Find seed entities in the graph
        seeds = self.seed_linker.find_seeds(question, graph)

        # 2. Graph traversal (C3 / C4)
        traversal = self.traverser.traverse(question, seeds, graph)

        # 3. Assemble context from traversal
        context = self.context_assembler.assemble(traversal, graph)

        # 4. Generate answer
        answer_obj: GeneratedAnswer = await self.answer_generator.generate(question, context)

        total_latency = time.perf_counter() - t_start

        # 5. Evaluate against gold answer
        metrics = (
            evaluate_answer(answer_obj.answer, gold_answer)
            if gold_answer
            else {"exact_match": 0.0, "token_f1": 0.0, "rouge_l": 0.0}
        )

        result = QueryResult(
            query_id=query_id,
            question=question,
            gold_answer=gold_answer,
            predicted_answer=answer_obj.answer,
            context=context,
            exact_match=metrics["exact_match"],
            token_f1=metrics["token_f1"],
            rouge_l=metrics["rouge_l"],
            nodes_visited=traversal.nodes_visited,
            traversal_depth=traversal.traversal_depth,
            prompt_tokens=answer_obj.prompt_tokens,
            completion_tokens=answer_obj.completion_tokens,
            latency_seconds=total_latency,
            strategy=traversal.strategy,
            variant=self.config.variant_name,
            dataset=dataset,
            metadata=traversal.metadata,
        )

        logger.info(
            "query_complete",
            query_id=query_id,
            em=result.exact_match,
            f1=result.token_f1,
            nodes_visited=traversal.nodes_visited,
            latency_s=round(total_latency, 2),
        )
        return result
