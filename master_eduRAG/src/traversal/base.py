"""
Graph traversal strategies.

base.py: Abstract Traverser interface
fixed_hop.py: K-hop traversal (baseline)
rlm_traverser.py: RLM REPL-guided traversal (C3)
parallel_dispatcher.py: Multi-entity async traversal with convergence scoring (C4)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.graph.knowledge_graph import KnowledgeGraph, Triple


@dataclass
class TraversalResult:
    """Result from any traversal strategy."""
    seed_entities: list[str]
    retrieved_triples: list[Triple]
    nodes_visited: int
    traversal_depth: int
    strategy: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_context_text(self, max_triples: int = 100) -> str:
        """Serialize triples to text context for LLM consumption."""
        lines: list[str] = []
        seen: set[str] = set()
        for triple in sorted(
            self.retrieved_triples[:max_triples],
            key=lambda t: t.confidence,
            reverse=True,
        ):
            text = triple.to_text()
            if text not in seen:
                lines.append(text)
                seen.add(text)
        return "\n".join(lines)


class Traverser(ABC):
    """Abstract traversal strategy."""

    @abstractmethod
    def traverse(
        self,
        query: str,
        seed_entities: list[str],
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        """
        Traverse the graph starting from seed entities.

        Args:
            query: Original user query.
            seed_entities: Starting entity IDs.
            graph: The knowledge graph.

        Returns:
            TraversalResult with collected triples.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        ...


# ---------------------------------------------------------------------------
# Fixed K-Hop Traversal (Baseline)
# ---------------------------------------------------------------------------


class FixedHopTraverser(Traverser):
    """
    Baseline K-hop traversal.
    Walks exactly K hops from seed entities without any intelligence.
    """

    def __init__(self, k: int = 3, min_confidence: float = 0.0) -> None:
        self.k = k
        self.min_confidence = min_confidence

    def get_name(self) -> str:
        return f"fixed_hop_k{self.k}"

    def traverse(
        self,
        query: str,
        seed_entities: list[str],
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        if not seed_entities:
            return TraversalResult(
                seed_entities=[], retrieved_triples=[],
                nodes_visited=0, traversal_depth=0, strategy=self.get_name()
            )

        all_triples: list[Triple] = []
        for seed in seed_entities:
            triples = graph.get_subgraph(
                [seed],
                depth=self.k,
                min_confidence=self.min_confidence,
            )
            all_triples.extend(triples)

        # Deduplicate
        seen: set[str] = set()
        unique_triples: list[Triple] = []
        for t in all_triples:
            key = f"{t.subject}|{t.relation}|{t.obj}"
            if key not in seen:
                seen.add(key)
                unique_triples.append(t)

        return TraversalResult(
            seed_entities=seed_entities,
            retrieved_triples=unique_triples,
            nodes_visited=len({t.subject for t in unique_triples} | {t.obj for t in unique_triples}),
            traversal_depth=self.k,
            strategy=self.get_name(),
        )
