"""
Community Detection Implementations.

leiden.py: Standard Leiden (structural, baseline)
cw_leiden.py: Confidence-Weighted Leiden (C2a - novel contribution)
rlm_community.py: RLM-guided semantic communities (C2b - novel contribution)

All in one module for brevity; each class is independently importable.
"""
from __future__ import annotations

import asyncio
from typing import Any

from src.community.base import CommunityDetector
from src.graph.knowledge_graph import KnowledgeGraph
from src.utils.config import CommunityConfig
from src.utils.llm_client import LLMClient
from src.utils.logger import get_logger

logger = get_logger("community")


# ---------------------------------------------------------------------------
# C2 Baseline: Standard Leiden
# ---------------------------------------------------------------------------


class LeidenDetector(CommunityDetector):
    """
    Standard Leiden algorithm using structural modularity.
    This is the baseline (no confidence weighting).
    """

    def __init__(self, config: CommunityConfig) -> None:
        self.config = config.leiden

    def get_name(self) -> str:
        return "leiden"

    def detect(self, graph: KnowledgeGraph) -> dict[str, int]:
        try:
            import igraph as ig  # type: ignore
            from cdlib import algorithms  # type: ignore

            g_nx = graph.to_networkx()
            if g_nx.number_of_nodes() == 0:
                return {}

            # Convert to igraph (cdlib uses igraph internally for Leiden)
            nodes = list(g_nx.nodes())
            node_idx = {n: i for i, n in enumerate(nodes)}
            edges = [(node_idx[u], node_idx[v]) for u, v in g_nx.edges()]

            ig_graph = ig.Graph(n=len(nodes), edges=edges, directed=False)
            result = algorithms.leiden(
                ig_graph,
                weights=None,
            )
            communities: dict[str, int] = {}
            for community_id, members in enumerate(result.communities):
                for member_idx in members:
                    communities[nodes[member_idx]] = community_id

            logger.info("leiden_complete", num_communities=len(result.communities))
            return communities

        except ImportError:
            logger.warning("leiden_deps_missing", msg="pip install cdlib igraph leidenalg")
            return self._fallback_connected_components(graph)
        except Exception as e:
            logger.error("leiden_failed", error=str(e))
            return self._fallback_connected_components(graph)

    @staticmethod
    def _fallback_connected_components(graph: KnowledgeGraph) -> dict[str, int]:
        """Fallback: use connected components as communities."""
        import networkx as nx
        g = graph.to_networkx().to_undirected()
        communities: dict[str, int] = {}
        for cid, component in enumerate(nx.connected_components(g)):
            for node in component:
                communities[node] = cid
        logger.info("fallback_cc_communities", num_communities=len(set(communities.values())))
        return communities


# ---------------------------------------------------------------------------
# C2a: Confidence-Weighted Leiden
# ---------------------------------------------------------------------------


class CWLeidenDetector(CommunityDetector):
    """
    Contribution 2a: Confidence-Weighted Leiden.

    Uses C(t) edge weights instead of uniform weights.
    Communities are formed by maximizing weighted modularity.
    High-confidence edges create strong community bonds;
    low-confidence edges carry less influence on structure.
    """

    def __init__(self, config: CommunityConfig) -> None:
        self.config = config.cw_leiden

    def get_name(self) -> str:
        return "cw_leiden"

    def detect(self, graph: KnowledgeGraph) -> dict[str, int]:
        try:
            import igraph as ig  # type: ignore
            from cdlib import algorithms  # type: ignore

            g_nx = graph.to_networkx()
            if g_nx.number_of_nodes() == 0:
                return {}

            nodes = list(g_nx.nodes())
            node_idx = {n: i for i, n in enumerate(nodes)}
            edges = []
            weights: list[float] = []

            for u, v, data in g_nx.edges(data=True):
                edges.append((node_idx[u], node_idx[v]))
                # Use confidence as edge weight; default 0.5 for unscored edges
                w = float(data.get(self.config.weight_attribute, 0.5))
                weights.append(max(0.001, w))  # Leiden requires positive weights

            ig_graph = ig.Graph(
                n=len(nodes),
                edges=edges,
                directed=False,
                edge_attrs={"weight": weights},
            )

            result = algorithms.leiden(
                ig_graph,
                weights="weight",
            )

            communities: dict[str, int] = {}
            for community_id, members in enumerate(result.communities):
                for member_idx in members:
                    communities[nodes[member_idx]] = community_id

            # Compute weighted modularity quality
            wq = result.newman_girvan_modularity().score if hasattr(result, "newman_girvan_modularity") else None
            logger.info(
                "cw_leiden_complete",
                num_communities=len(result.communities),
                weighted_modularity=wq,
            )
            return communities

        except ImportError:
            logger.warning("cw_leiden_deps_missing", msg="pip install cdlib igraph leidenalg")
            return LeidenDetector._fallback_connected_components(graph)
        except Exception as e:
            logger.error("cw_leiden_failed", error=str(e))
            return LeidenDetector._fallback_connected_components(graph)


# ---------------------------------------------------------------------------
# C2b: RLM-Guided Semantic Community Detection
# ---------------------------------------------------------------------------

RLM_COMMUNITY_PROMPT = """You are a knowledge graph expert assigning semantic community labels.

Below are entities from a knowledge graph, along with their top neighbors:

{entity_neighborhoods}

Task: Group these entities into semantically coherent communities.
Two entities should be in the same community if they are about the same topic or concept.
Ignore connections that appear coincidental (e.g., entities linked only because they appear on the same page).

Return ONLY a JSON object mapping entity names to integer community IDs (0-indexed):
{{
  "entity_name_1": 0,
  "entity_name_2": 0,
  "entity_name_3": 1,
  ...
}}

Be conservative: prefer fewer, more coherent communities over many small ones."""


class RLMCommunityDetector(CommunityDetector):
    """
    Contribution 2b: RLM-Guided Semantic Community Detection.

    Instead of optimizing structural modularity, an LLM reads
    entity neighborhoods and assigns communities based on
    semantic understanding. Produces semantically coherent communities
    at the cost of higher compute.

    Best used for small-to-medium graphs (< 5000 nodes).
    For larger graphs, use CWLeidenDetector.
    """

    def __init__(self, config: CommunityConfig, llm_client: LLMClient) -> None:
        self.config = config.rlm_community
        self.llm = llm_client

    def get_name(self) -> str:
        return "rlm_community"

    def detect(self, graph: KnowledgeGraph) -> dict[str, int]:
        """Run LLM-based community detection synchronously."""
        return asyncio.run(self._detect_async(graph))

    async def _detect_async(self, graph: KnowledgeGraph) -> dict[str, int]:
        entities = graph.get_all_entities()
        if not entities:
            return {}

        batch_size = self.config.max_entities_per_call
        all_assignments: dict[str, int] = {}
        community_offset = 0

        # Process in batches to stay within context limits
        for i in range(0, len(entities), batch_size):
            batch = entities[i: i + batch_size]
            neighborhoods = self._build_neighborhood_description(batch, graph)

            prompt = RLM_COMMUNITY_PROMPT.format(entity_neighborhoods=neighborhoods)
            response = await self.llm.generate(prompt, context_label="rlm_community")

            batch_assignments = self._parse_community_response(response.content, batch)
            # Offset community IDs to avoid collision across batches
            max_id = max(batch_assignments.values(), default=-1)
            for entity, cid in batch_assignments.items():
                all_assignments[entity] = cid + community_offset
            community_offset += max_id + 1

        logger.info(
            "rlm_community_complete",
            num_entities=len(entities),
            num_communities=len(set(all_assignments.values())),
        )
        return all_assignments

    def _build_neighborhood_description(
        self, entities: list[str], graph: KnowledgeGraph
    ) -> str:
        """Build a text description of each entity's neighborhood."""
        lines: list[str] = []
        for entity in entities:
            neighbors = graph.get_neighbors(
                entity, min_confidence=self.config.similarity_threshold
            )[:5]  # top 5 neighbors
            neighbor_str = ", ".join(n["entity"] for n in neighbors) if neighbors else "(isolated)"
            lines.append(f"- {entity}: connected to [{neighbor_str}]")
        return "\n".join(lines)

    @staticmethod
    def _parse_community_response(response: str, entities: list[str]) -> dict[str, int]:
        """Parse LLM community assignment response."""
        import json
        import re

        try:
            clean = re.sub(r"```(?:json)?", "", response).strip().rstrip("`").strip()
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                data = json.loads(match.group())
                assignments: dict[str, int] = {}
                for entity in entities:
                    if entity in data:
                        assignments[entity] = int(data[entity])
                    else:
                        # Try case-insensitive match
                        for key, val in data.items():
                            if key.lower() == entity.lower():
                                assignments[entity] = int(val)
                                break
                        else:
                            assignments[entity] = 0  # default community
                return assignments
        except Exception as e:
            logger.warning("community_parse_failed", error=str(e))

        # Fallback: assign all to community 0
        return {e: 0 for e in entities}


def build_community_detector(
    config: CommunityConfig,
    llm_client: LLMClient | None = None,
) -> CommunityDetector:
    """
    Factory function: instantiate the correct detector from config.

    Args:
        config: CommunityConfig with strategy field.
        llm_client: Required only for rlm_community strategy.

    Returns:
        Concrete CommunityDetector instance.
    """
    strategy = config.strategy
    if strategy == "leiden":
        return LeidenDetector(config)
    elif strategy == "cw_leiden":
        return CWLeidenDetector(config)
    elif strategy == "rlm_community":
        if llm_client is None:
            raise ValueError("llm_client required for rlm_community strategy")
        return RLMCommunityDetector(config, llm_client)
    else:
        raise ValueError(f"Unknown community strategy: {strategy}")
