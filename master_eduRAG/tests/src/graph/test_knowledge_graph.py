"""Tests for the core NetworkX-backed knowledge graph."""

from src.graph.knowledge_graph import KnowledgeGraph, Triple


def test_add_triples_and_query_neighbors():
    graph = KnowledgeGraph()
    graph.add_triples([
        Triple("Python", "uses", "Indentation", confidence=0.9),
        Triple("Indentation", "improves", "Readability", confidence=0.7),
    ])

    assert graph.entity_exists("python")
    assert graph.summary()["num_nodes"] == 3
    assert graph.get_neighbors("python")[0]["entity"] == "indentation"


def test_confidence_filtering_and_paths():
    graph = KnowledgeGraph()
    graph.add_triples([
        Triple("A", "strong", "B", confidence=0.8),
        Triple("B", "weak", "C", confidence=0.2),
    ])

    assert graph.get_high_confidence_triples(0.5)[0].relation == "strong"
    assert graph.get_path("A", "C") == [("a", "strong", "b"), ("b", "weak", "c")]
    assert graph.get_path("A", "missing") is None


def test_empty_and_duplicate_triples_are_handled():
    graph = KnowledgeGraph()
    graph.add_triples([
        Triple("", "ignored", "B"),
        Triple("A", "low", "B", confidence=0.2),
        Triple("A", "high", "B", confidence=0.9),
    ])

    assert graph.summary()["num_edges"] == 1
    assert graph.get_high_confidence_triples(0.5)[0].relation == "high"
