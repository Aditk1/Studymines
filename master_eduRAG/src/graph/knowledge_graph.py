"""
Core KnowledgeGraph data structure.
A NetworkX DiGraph wrapper with confidence-weighted edges,
community assignments, and node embeddings.
"""
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np

from src.utils.logger import get_logger

logger = get_logger("knowledge_graph")


@dataclass
class Triple:
    """A single extracted knowledge triple."""
    subject: str
    relation: str
    obj: str
    confidence: float = 1.0
    source_chunk: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        return f"({self.subject}, {self.relation}, {self.obj})"


@dataclass
class NodeData:
    """Data stored on each graph node."""
    label: str
    community: int = -1
    embedding: list[float] = field(default_factory=list)
    mention_count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """
    Confidence-weighted, community-annotated Knowledge Graph.

    Wraps NetworkX DiGraph with research-specific primitives
    designed to be accessible from the RLM REPL environment.

    Nodes: entities (string IDs)
    Edges: (subject, object) with attributes:
        - relation: str
        - confidence: float   ← C(t) from C1 scorer
        - source_chunk: str
    """

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()
        self.stats: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Building
    # ------------------------------------------------------------------

    def add_triple(self, triple: Triple) -> None:
        """Add a triple to the graph. Creates nodes if they don't exist."""
        s = triple.subject.strip().lower()
        o = triple.obj.strip().lower()

        if not s or not o:
            return

        # Add / update nodes
        for entity in (s, o):
            if entity not in self._g:
                self._g.add_node(entity, label=entity, community=-1, embedding=[], mention_count=1)
            else:
                self._g.nodes[entity]["mention_count"] = self._g.nodes[entity].get("mention_count", 1) + 1

        # Add / update edge (take max confidence if edge exists)
        if self._g.has_edge(s, o):
            existing = self._g[s][o].get("confidence", 0.0)
            if triple.confidence > existing:
                self._g[s][o]["confidence"] = triple.confidence
                self._g[s][o]["relation"] = triple.relation
        else:
            self._g.add_edge(
                s,
                o,
                relation=triple.relation,
                confidence=triple.confidence,
                source_chunk=triple.source_chunk,
            )

    def add_triples(self, triples: list[Triple]) -> None:
        """Batch add triples."""
        for t in triples:
            self.add_triple(t)
        self._update_stats()

    def set_node_embedding(self, entity: str, embedding: list[float]) -> None:
        entity = entity.lower()
        if entity in self._g:
            self._g.nodes[entity]["embedding"] = embedding

    def set_community(self, entity: str, community_id: int) -> None:
        entity = entity.lower()
        if entity in self._g:
            self._g.nodes[entity]["community"] = community_id

    # ------------------------------------------------------------------
    # Graph Primitives (exposed to RLM REPL)
    # ------------------------------------------------------------------

    def get_neighbors(
        self,
        entity: str,
        min_confidence: float = 0.0,
        include_incoming: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Return neighbors of an entity, optionally filtered by confidence.

        Args:
            entity: Entity string (case-insensitive).
            min_confidence: Minimum edge confidence to include.
            include_incoming: If True, include both in and out neighbors.

        Returns:
            List of dicts: {entity, relation, confidence, direction}
        """
        entity = entity.strip().lower()
        if entity not in self._g:
            return []

        neighbors: list[dict[str, Any]] = []

        # Outgoing edges
        for _, neighbor, data in self._g.out_edges(entity, data=True):
            if data.get("confidence", 0.0) >= min_confidence:
                neighbors.append({
                    "entity": neighbor,
                    "relation": data.get("relation", ""),
                    "confidence": round(data.get("confidence", 0.0), 4),
                    "direction": "outgoing",
                })

        # Incoming edges
        if include_incoming:
            for source, _, data in self._g.in_edges(entity, data=True):
                if data.get("confidence", 0.0) >= min_confidence:
                    neighbors.append({
                        "entity": source,
                        "relation": f"inverse:{data.get('relation', '')}",
                        "confidence": round(data.get("confidence", 0.0), 4),
                        "direction": "incoming",
                    })

        return sorted(neighbors, key=lambda x: x["confidence"], reverse=True)

    def get_path(
        self,
        entity_a: str,
        entity_b: str,
        max_hops: int = 5,
    ) -> list[tuple[str, str, str]] | None:
        """
        Find shortest path between two entities.

        Returns:
            List of (node_a, relation, node_b) triples along the path,
            or None if no path exists.
        """
        a = entity_a.strip().lower()
        b = entity_b.strip().lower()
        try:
            path_nodes = nx.shortest_path(self._g.to_undirected(), a, b, weight=None)
            if len(path_nodes) > max_hops + 1:
                return None
            triples = []
            for i in range(len(path_nodes) - 1):
                u, v = path_nodes[i], path_nodes[i + 1]
                if self._g.has_edge(u, v):
                    rel = self._g[u][v].get("relation", "related_to")
                elif self._g.has_edge(v, u):
                    rel = f"inverse:{self._g[v][u].get('relation', 'related_to')}"
                else:
                    rel = "related_to"
                triples.append((u, rel, v))
            return triples
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_community(self, entity: str) -> int:
        """Return the community ID of an entity, or -1 if unassigned."""
        entity = entity.strip().lower()
        if entity not in self._g:
            return -1
        return self._g.nodes[entity].get("community", -1)

    def get_community_members(self, community_id: int) -> list[str]:
        """Return all entities in a given community."""
        return [
            n for n, d in self._g.nodes(data=True)
            if d.get("community", -1) == community_id
        ]

    def get_subgraph(
        self,
        entities: list[str],
        depth: int = 1,
        min_confidence: float = 0.0,
    ) -> list[Triple]:
        """
        Extract a subgraph centered on given entities up to `depth` hops.

        Returns:
            List of Triple objects in the subgraph.
        """
        seed_set = {e.strip().lower() for e in entities}
        visited: set[str] = set()
        frontier = set(seed_set)

        for _ in range(depth):
            next_frontier: set[str] = set()
            for entity in frontier:
                if entity in visited:
                    continue
                visited.add(entity)
                for _, neighbor, data in self._g.out_edges(entity, data=True):
                    if data.get("confidence", 0.0) >= min_confidence:
                        next_frontier.add(neighbor)
                for source, _, data in self._g.in_edges(entity, data=True):
                    if data.get("confidence", 0.0) >= min_confidence:
                        next_frontier.add(source)
            frontier = next_frontier - visited

        all_nodes = visited | frontier
        triples: list[Triple] = []
        for u, v, data in self._g.edges(data=True):
            if u in all_nodes and v in all_nodes:
                if data.get("confidence", 0.0) >= min_confidence:
                    triples.append(Triple(
                        subject=u,
                        relation=data.get("relation", ""),
                        obj=v,
                        confidence=data.get("confidence", 0.0),
                        source_chunk=data.get("source_chunk", ""),
                    ))
        return triples

    def get_high_confidence_triples(self, min_confidence: float = 0.5) -> list[Triple]:
        """Return all triples above a confidence threshold."""
        return [
            Triple(
                subject=u, relation=d.get("relation", ""), obj=v,
                confidence=d.get("confidence", 0.0),
                source_chunk=d.get("source_chunk", ""),
            )
            for u, v, d in self._g.edges(data=True)
            if d.get("confidence", 0.0) >= min_confidence
        ]

    def entity_exists(self, entity: str) -> bool:
        return entity.strip().lower() in self._g

    def get_all_entities(self) -> list[str]:
        return list(self._g.nodes())

    def get_all_communities(self) -> set[int]:
        return {d.get("community", -1) for _, d in self._g.nodes(data=True)}

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """Save graph to disk using pickle."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            pickle.dump({"graph": self._g, "stats": self.stats}, f)
        logger.info("graph_saved", path=str(path), nodes=self._g.number_of_nodes())

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeGraph":
        """Load graph from disk."""
        path = Path(path)
        kg = cls()
        with path.open("rb") as f:
            data = pickle.load(f)
        kg._g = data["graph"]
        kg.stats = data.get("stats", {})
        logger.info("graph_loaded", path=str(path), nodes=kg._g.number_of_nodes())
        return kg

    def to_networkx(self) -> nx.DiGraph:
        """Return raw NetworkX graph (for community algorithms)."""
        return self._g

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def _update_stats(self) -> None:
        g = self._g
        confidences = [d.get("confidence", 0.0) for _, _, d in g.edges(data=True)]
        self.stats = {
            "num_nodes": g.number_of_nodes(),
            "num_edges": g.number_of_edges(),
            "avg_confidence": float(np.mean(confidences)) if confidences else 0.0,
            "min_confidence": float(np.min(confidences)) if confidences else 0.0,
            "max_confidence": float(np.max(confidences)) if confidences else 0.0,
            "num_communities": len(self.get_all_communities() - {-1}),
            "density": nx.density(g),
        }

    def summary(self) -> dict[str, Any]:
        self._update_stats()
        return self.stats

    def __repr__(self) -> str:
        return (
            f"KnowledgeGraph(nodes={self._g.number_of_nodes()}, "
            f"edges={self._g.number_of_edges()})"
        )
