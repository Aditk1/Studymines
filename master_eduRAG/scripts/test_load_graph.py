"""
Developer smoke script for loading serialized graph artifacts.
"""


import json
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.graph.knowledge_graph import KnowledgeGraph

graph_path = PROJECT_ROOT / "data" / "graphs" / "graph_HTML_CSS_Complete_Guide.pkl"

try:
    kg = KnowledgeGraph.load(str(graph_path))
    print(f"Loaded KnowledgeGraph: {kg}")
    print(f"Nodes: {kg._g.number_of_nodes()}")
    print(f"Edges: {kg._g.number_of_edges()}")
    print(f"Stats: {kg.summary()}")
except Exception as e:
    print(f"Error loading graph: {e}")
