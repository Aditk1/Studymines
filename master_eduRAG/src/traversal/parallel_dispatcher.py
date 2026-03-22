"""
Contribution 4: Multi-Entity Parallel Traversal with Convergence Scoring.

For multi-entity queries, spawns parallel RLM sub-calls (one per seed entity)
using asyncio. Nodes that appear in multiple traversal paths receive a
convergence score — they are the semantically central context for the query.

Convergence score: freq(node) * avg_confidence_of_paths_reaching_node
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from src.graph.knowledge_graph import KnowledgeGraph, Triple
from src.traversal.base import TraversalResult, Traverser
from src.utils.config import ParallelConfig
from src.utils.logger import get_logger

logger = get_logger("parallel_dispatcher")


@dataclass
class ConvergenceScore:
    """Convergence information for a single node."""
    entity: str
    path_count: int        # how many traversal paths reached this node
    avg_confidence: float  # avg confidence of edges in paths that reached it
    convergence_score: float  # final ranking score


@dataclass
class ParallelTraversalResult(TraversalResult):
    """Extended result with convergence data."""
    per_entity_results: dict[str, TraversalResult] = field(default_factory=dict)
    convergence_scores: list[ConvergenceScore] = field(default_factory=list)
    convergence_nodes: list[str] = field(default_factory=list)


class ConvergenceScorer:
    """
    Computes convergence scores from parallel traversal results.

    A convergence node is one that appears in multiple independent
    traversal paths — indicating it is semantically central to
    bridging multiple query entities.
    """

    def __init__(
        self,
        min_paths: int = 2,
        weight_by_confidence: bool = True,
    ) -> None:
        self.min_paths = min_paths
        self.weight_by_confidence = weight_by_confidence

    def score(
        self,
        results: dict[str, TraversalResult],
    ) -> list[ConvergenceScore]:
        """
        Score all nodes by how many traversal paths reached them.

        Args:
            results: Dict mapping seed_entity → TraversalResult.

        Returns:
            List of ConvergenceScore objects, sorted by convergence_score descending.
        """
        # node → list of (path_confidence) for each path that reached it
        node_path_confidences: dict[str, list[float]] = defaultdict(list)

        for seed, result in results.items():
            # Collect nodes in this path
            path_nodes: dict[str, list[float]] = defaultdict(list)
            for triple in result.retrieved_triples:
                path_nodes[triple.subject].append(triple.confidence)
                path_nodes[triple.obj].append(triple.confidence)

            for node, confs in path_nodes.items():
                avg_conf = sum(confs) / len(confs) if confs else 0.0
                node_path_confidences[node].append(avg_conf)

        convergence_scores: list[ConvergenceScore] = []
        for node, path_confs in node_path_confidences.items():
            path_count = len(path_confs)
            if path_count < self.min_paths:
                continue

            avg_confidence = sum(path_confs) / path_count

            if self.weight_by_confidence:
                score = path_count * avg_confidence
            else:
                score = float(path_count)

            convergence_scores.append(ConvergenceScore(
                entity=node,
                path_count=path_count,
                avg_confidence=round(avg_confidence, 4),
                convergence_score=round(score, 4),
            ))

        convergence_scores.sort(key=lambda x: x.convergence_score, reverse=True)
        return convergence_scores


class ParallelDispatcher(Traverser):
    """
    Contribution 4: Multi-Entity Parallel Traversal with Convergence Scoring.

    Spawns one RLM traversal per seed entity concurrently using asyncio.
    After all paths complete, scores nodes by convergence (appearing
    in multiple paths) and assembles a converged context.

    Falls back to single-entity traversal if parallel is disabled
    or only one seed entity is provided.
    """

    def __init__(
        self,
        config: ParallelConfig,
        single_traverser: Traverser,
    ) -> None:
        self.config = config
        self.single_traverser = single_traverser
        self.convergence_scorer = ConvergenceScorer(
            min_paths=config.convergence_min_paths,
            weight_by_confidence=config.convergence_weight_by_confidence,
        )

    def get_name(self) -> str:
        base = self.single_traverser.get_name()
        return f"parallel_{base}_convergence"

    def traverse(
        self,
        query: str,
        seed_entities: list[str],
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        """Synchronous entry point."""
        if not self.config.enabled or len(seed_entities) <= 1:
            return self.single_traverser.traverse(query, seed_entities, graph)

        try:
            return asyncio.run(self._parallel_traverse(query, seed_entities, graph))
        except Exception as e:
            logger.error("parallel_dispatch_failed", error=str(e), falling_back=True)
            return self.single_traverser.traverse(query, seed_entities, graph)

    async def _parallel_traverse(
        self,
        query: str,
        seed_entities: list[str],
        graph: KnowledgeGraph,
    ) -> ParallelTraversalResult:
        """
        Core parallel traversal logic.

        Limits concurrency to max_concurrent_entities to avoid
        overwhelming the LLM backend on laptop hardware.
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent_entities)
        limited_seeds = seed_entities[: self.config.max_concurrent_entities * 2]

        async def traverse_one(seed: str) -> tuple[str, TraversalResult]:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        self._async_single_traverse(query, [seed], graph),
                        timeout=self.config.async_timeout,
                    )
                    return seed, result
                except asyncio.TimeoutError:
                    logger.warning("traversal_timeout", seed=seed)
                    return seed, TraversalResult(
                        seed_entities=[seed], retrieved_triples=[],
                        nodes_visited=0, traversal_depth=0,
                        strategy="timeout"
                    )

        tasks = [traverse_one(seed) for seed in limited_seeds]
        raw_results = await asyncio.gather(*tasks)
        per_entity: dict[str, TraversalResult] = dict(raw_results)

        # Score convergence
        convergence_scores = self.convergence_scorer.score(per_entity)
        convergence_nodes = [cs.entity for cs in convergence_scores]

        # Assemble combined triple list
        # Priority: convergence nodes first, then all other triples
        all_triples: list[Triple] = []
        seen_keys: set[str] = set()
        total_nodes_visited = 0

        # First: triples involving convergence nodes
        for result in per_entity.values():
            total_nodes_visited += result.nodes_visited
            for triple in result.retrieved_triples:
                if triple.subject in convergence_nodes or triple.obj in convergence_nodes:
                    key = f"{triple.subject}|{triple.relation}|{triple.obj}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_triples.append(triple)

        # Then: remaining triples
        for result in per_entity.values():
            for triple in result.retrieved_triples:
                key = f"{triple.subject}|{triple.relation}|{triple.obj}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_triples.append(triple)

        # Sort by confidence
        all_triples.sort(key=lambda t: t.confidence, reverse=True)

        max_depth = max((r.traversal_depth for r in per_entity.values()), default=0)

        logger.info(
            "parallel_traversal_complete",
            num_seeds=len(limited_seeds),
            total_triples=len(all_triples),
            convergence_nodes=len(convergence_nodes),
            total_nodes_visited=total_nodes_visited,
        )

        return ParallelTraversalResult(
            seed_entities=limited_seeds,
            retrieved_triples=all_triples,
            nodes_visited=total_nodes_visited,
            traversal_depth=max_depth,
            strategy=self.get_name(),
            per_entity_results=per_entity,
            convergence_scores=convergence_scores,
            convergence_nodes=convergence_nodes,
            metadata={
                "num_convergence_nodes": len(convergence_nodes),
                "top_convergence": [
                    {"entity": cs.entity, "score": cs.convergence_score}
                    for cs in convergence_scores[:5]
                ],
            },
        )

    async def _async_single_traverse(
        self,
        query: str,
        seeds: list[str],
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        """Async wrapper for the single traverser."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.single_traverser.traverse(query, seeds, graph)
        )
