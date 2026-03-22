"""
Abstract base class for community detection strategies.
All implementations must follow this interface for swappable experiments.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.graph.knowledge_graph import KnowledgeGraph


class CommunityDetector(ABC):
    """
    Abstract community detector.

    Takes a KnowledgeGraph, assigns community IDs to all nodes,
    and returns both the mapping and quality metrics.
    """

    @abstractmethod
    def detect(self, graph: KnowledgeGraph) -> dict[str, int]:
        """
        Assign community IDs to nodes.

        Args:
            graph: The weighted knowledge graph (C(t) edge weights available).

        Returns:
            Dict mapping node_id (str) → community_id (int).
            Nodes that cannot be assigned receive community -1.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Return short identifier used in experiment logs and reports."""
        ...

    def apply(self, graph: KnowledgeGraph) -> dict[str, Any]:
        """
        Run detection and apply results to the graph.

        Returns:
            Dict with 'communities' mapping and quality info.
        """
        communities = self.detect(graph)
        num_assigned = 0
        for node, community_id in communities.items():
            graph.set_community(node, community_id)
            if community_id >= 0:
                num_assigned += 1

        unique = len(set(v for v in communities.values() if v >= 0))
        return {
            "strategy": self.get_name(),
            "num_communities": unique,
            "num_assigned_nodes": num_assigned,
            "community_mapping": communities,
        }
