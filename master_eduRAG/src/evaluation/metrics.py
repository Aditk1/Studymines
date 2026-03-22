"""
Evaluation metrics: EM, F1, ROUGE-L, graph quality, cost tracking.
"""
from __future__ import annotations

import re
import string
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.utils.logger import get_logger

logger = get_logger("evaluation")


def normalize_answer(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    text = "".join(c for c in text if c not in string.punctuation)
    return " ".join(text.split())


def exact_match(prediction: str, gold: str) -> float:
    return 1.0 if normalize_answer(prediction) == normalize_answer(gold) else 0.0


def token_f1(prediction: str, gold: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()
    if not pred_tokens or not gold_tokens:
        return 0.0
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_common = sum(common.values())
    if num_common == 0:
        return 0.0
    precision = num_common / len(pred_tokens)
    recall = num_common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def rouge_l(prediction: str, gold: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(gold).split()
    if not pred_tokens or not gold_tokens:
        return 0.0
    lcs = _lcs_length(pred_tokens, gold_tokens)
    precision = lcs / len(pred_tokens)
    recall = lcs / len(gold_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _lcs_length(a: list[str], b: list[str]) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for token in a:
        curr = [0] * (len(b) + 1)
        for j, bt in enumerate(b, 1):
            curr[j] = prev[j - 1] + 1 if token == bt else max(curr[j - 1], prev[j])
        prev = curr
    return prev[len(b)]


def evaluate_answer(prediction: str, gold: str) -> dict[str, float]:
    return {
        "exact_match": exact_match(prediction, gold),
        "token_f1": token_f1(prediction, gold),
        "rouge_l": rouge_l(prediction, gold),
    }


@dataclass
class QueryResult:
    query_id: str
    question: str
    gold_answer: str
    predicted_answer: str
    context: str
    exact_match: float
    token_f1: float
    rouge_l: float
    nodes_visited: int
    traversal_depth: int
    prompt_tokens: int
    completion_tokens: int
    latency_seconds: float
    strategy: str
    variant: str
    dataset: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "query_id": self.query_id,
            "question": self.question,
            "gold_answer": self.gold_answer,
            "predicted_answer": self.predicted_answer,
            "exact_match": self.exact_match,
            "token_f1": self.token_f1,
            "rouge_l": self.rouge_l,
            "nodes_visited": self.nodes_visited,
            "traversal_depth": self.traversal_depth,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "latency_seconds": self.latency_seconds,
            "strategy": self.strategy,
            "variant": self.variant,
            "dataset": self.dataset,
        }
        d.update(self.metadata)
        return d


def aggregate_results(results: list[QueryResult]) -> dict[str, Any]:
    if not results:
        return {}

    def mean(vals: list[float]) -> float:
        return round(float(np.mean(vals)), 4) if vals else 0.0

    return {
        "num_queries": len(results),
        "exact_match": mean([r.exact_match for r in results]),
        "token_f1": mean([r.token_f1 for r in results]),
        "rouge_l": mean([r.rouge_l for r in results]),
        "avg_nodes_visited": mean([float(r.nodes_visited) for r in results]),
        "avg_traversal_depth": mean([float(r.traversal_depth) for r in results]),
        "avg_prompt_tokens": mean([float(r.prompt_tokens) for r in results]),
        "avg_completion_tokens": mean([float(r.completion_tokens) for r in results]),
        "avg_latency_seconds": mean([r.latency_seconds for r in results]),
        "total_prompt_tokens": sum(r.prompt_tokens for r in results),
        "total_completion_tokens": sum(r.completion_tokens for r in results),
    }


def compute_community_coherence(graph: Any) -> dict[str, float]:
    """Mean pairwise cosine similarity within each community."""
    g = graph.to_networkx()
    community_embeddings: dict[int, list[list[float]]] = {}
    for node, data in g.nodes(data=True):
        cid = data.get("community", -1)
        emb = data.get("embedding", [])
        if cid >= 0 and emb:
            community_embeddings.setdefault(cid, []).append(emb)

    scores: list[float] = []
    for cid, embs in community_embeddings.items():
        if len(embs) < 2:
            scores.append(1.0)
            continue
        mat = np.array(embs)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        mat = mat / norms
        sim = mat @ mat.T
        upper = sim[np.triu_indices(len(embs), k=1)]
        scores.append(float(np.mean(upper)))

    return {
        "mean_coherence": round(float(np.mean(scores)), 4) if scores else 0.0,
        "num_communities": len(scores),
    }


def compute_weighted_modularity(graph: Any) -> float:
    try:
        import networkx as nx
        from networkx.algorithms.community.quality import modularity

        g = graph.to_networkx().to_undirected()
        if g.number_of_nodes() == 0:
            return 0.0
        community_map: dict[int, set] = {}
        for node, data in g.nodes(data=True):
            cid = data.get("community", -1)
            community_map.setdefault(cid, set()).add(node)
        communities = list(community_map.values())
        if len(communities) <= 1:
            return 0.0
        for u, v, data in g.edges(data=True):
            g[u][v]["weight"] = data.get("confidence", 1.0)
        return round(float(modularity(g, communities, weight="weight")), 4)
    except Exception as e:
        logger.warning("modularity_failed", error=str(e))
        return 0.0


@dataclass
class GraphQualityReport:
    strategy: str
    num_nodes: int
    num_edges: int
    num_communities: int
    weighted_modularity: float
    mean_community_coherence: float
    avg_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "num_communities": self.num_communities,
            "weighted_modularity": self.weighted_modularity,
            "mean_community_coherence": self.mean_community_coherence,
            "avg_confidence": self.avg_confidence,
        }


def evaluate_graph_quality(graph: Any, strategy_name: str) -> GraphQualityReport:
    stats = graph.summary()
    coherence = compute_community_coherence(graph)
    mod = compute_weighted_modularity(graph)
    return GraphQualityReport(
        strategy=strategy_name,
        num_nodes=stats.get("num_nodes", 0),
        num_edges=stats.get("num_edges", 0),
        num_communities=stats.get("num_communities", 0),
        weighted_modularity=mod,
        mean_community_coherence=coherence.get("mean_coherence", 0.0),
        avg_confidence=stats.get("avg_confidence", 0.0),
    )
