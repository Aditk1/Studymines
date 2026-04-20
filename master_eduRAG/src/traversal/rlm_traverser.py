"""
Contribution 3: RLM-Guided Graph Traversal via Python REPL.

The LLM receives the knowledge graph as an environment variable
and writes Python code to navigate it — deciding which neighbors
to follow, when to recurse, and when to stop.

This is a faithful implementation of the RLM pattern adapted for
graph traversal. The graph primitives are exposed as a Python object
within the execution context.
"""
from __future__ import annotations

import asyncio
import textwrap
import traceback
from typing import Any

from src.graph.knowledge_graph import KnowledgeGraph, Triple
from src.traversal.base import FixedHopTraverser, TraversalResult, Traverser
from src.utils.config import TraversalConfig
from src.utils.llm_client import LLMClient
from src.utils.logger import get_logger

logger = get_logger("rlm_traverser")

# -------------------------------------------------------------------------
# System prompt given to the RLM at the start of each traversal
# -------------------------------------------------------------------------

RLM_SYSTEM_PROMPT = """You are a knowledge graph navigator. You have access to a knowledge graph 
via Python. Your job is to find the most relevant information to answer a query.

Available graph functions:
  graph.get_neighbors(entity, min_confidence=0.0)
    → returns list of {entity, relation, confidence, direction}
  
  graph.get_path(entity_a, entity_b, max_hops=5)
    → returns list of (node_a, relation, node_b) or None
  
  graph.get_community(entity)
    → returns community_id (int)
  
  graph.get_community_members(community_id)
    → returns list of entity strings
  
  graph.get_subgraph(entities, depth=1, min_confidence=0.0)
    → returns list of Triple objects with .subject, .relation, .obj, .confidence

Rules:
1. Write Python code that explores the graph to find relevant triples.
2. Store discovered triples in the list: `collected_triples`
3. You have up to {max_steps} exploration steps.
4. Prefer high-confidence edges (confidence >= {min_conf}).
5. Stop when you have enough context or reach max depth {max_depth}.
6. Think step by step in comments before writing code.
"""

# -------------------------------------------------------------------------
# Per-step prompt template
# -------------------------------------------------------------------------

RLM_STEP_PROMPT = """Query: {query}
Seed entities: {seeds}
Current collected triples ({n_collected}): {sample_triples}
Steps remaining: {steps_remaining}

What Python code should I run next to find more relevant context?
If you have enough information, write: `DONE`
Otherwise, write executable Python code that adds triples to `collected_triples`.

Example:
```python
neighbors = graph.get_neighbors("backpropagation", min_confidence=0.4)
for n in neighbors[:5]:
    triples = graph.get_subgraph([n["entity"]], depth=1, min_confidence=0.4)
    collected_triples.extend(triples)
```
"""


class GraphREPL:
    """
    A restricted Python execution environment that exposes
    the KnowledgeGraph to the RLM.
    Collects discovered triples in `collected_triples`.
    """

    def __init__(self, graph: KnowledgeGraph, min_confidence: float = 0.0) -> None:
        self.graph = graph
        self.min_confidence = min_confidence
        self.collected_triples: list[Triple] = []
        self.nodes_visited: set[str] = set()
        self._exec_count = 0

    def execute(self, code: str) -> str:
        """
        Execute safe graph operations in the graph context.
        Replaces unsafe exec() with a controlled dispatcher.

        Args:
            code: Text from LLM suggesting operations.

        Returns:
            String status message.
        """
        self._exec_count += 1
        
        # Simple parser for the allowed functions
        import re
        
        operations_performed = []
        
        try:
            # 1. Look for neighbors calls: graph.get_neighbors("entity", min_confidence=0.4)
            neighbor_matches = re.finditer(r'graph\.get_neighbors\("([^"]+)"(?:,\s*min_confidence=([\d\.]+))?\)', code)
            for m in neighbor_matches:
                entity = m.group(1)
                conf = float(m.group(2)) if m.group(2) else self.min_confidence
                neighbors = self.graph.get_neighbors(entity, min_confidence=conf)
                # Auto-expand subgraph for found neighbors to fill collected_triples
                for n in neighbors[:5]:
                    triples = self.graph.get_subgraph([n["entity"]], depth=1, min_confidence=conf)
                    self.collected_triples.extend(triples)
                operations_performed.append(f"Explored neighbors of '{entity}'")

            # 2. Look for subgraph calls: graph.get_subgraph(["entity"], depth=1)
            subgraph_matches = re.finditer(r'graph\.get_subgraph\(\["([^"]+)"\](?:,\s*depth=(\d+))?(?:,\s*min_confidence=([\d\.]+))?\)', code)
            for m in subgraph_matches:
                entity = m.group(1)
                depth = int(m.group(2)) if m.group(2) else 1
                conf = float(m.group(3)) if m.group(3) else self.min_confidence
                triples = self.graph.get_subgraph([entity], depth=depth, min_confidence=conf)
                self.collected_triples.extend(triples)
                operations_performed.append(f"Retrieved subgraph for '{entity}' at depth {depth}")

            # 3. Look for path calls: graph.get_path("a", "b")
            path_matches = re.finditer(r'graph\.get_path\("([^"]+)",\s*"([^"]+)"\)', code)
            for m in path_matches:
                a, b = m.groups()
                triples = self.graph.get_path(a, b)
                if triples:
                    self.collected_triples.extend(triples)
                    operations_performed.append(f"Found path between '{a}' and '{b}'")

            # Track visited nodes
            for t in self.collected_triples:
                self.nodes_visited.add(t.subject)
                self.nodes_visited.add(t.obj)

            if not operations_performed:
                return "OK - (No matching operations found in output)"
            return "OK: " + "; ".join(operations_performed)
            
        except Exception as e:
            logger.debug("repl_safe_exec_error", error=str(e))
            return f"ERROR: {str(e)}"

    def get_state_summary(self) -> str:
        """Return a brief summary of current state for the LLM prompt."""
        n = len(self.collected_triples)
        if n == 0:
            return "none"
        sample = self.collected_triples[:3]
        return "; ".join(t.to_text() for t in sample) + (f" ... +{n - 3} more" if n > 3 else "")


class RLMTraverser(Traverser):
    """
    Contribution 3: RLM-Guided Graph Traversal.

    The LLM programs against the graph via a Python REPL,
    making intelligent decisions about which paths to follow
    based on semantic relevance to the query.
    """

    def __init__(self, config: TraversalConfig, llm_client: LLMClient) -> None:
        self.config = config.rlm
        self.llm = llm_client
        self._fallback = FixedHopTraverser(k=3)

    def get_name(self) -> str:
        return "rlm_traversal"

    def traverse(
        self,
        query: str,
        seed_entities: list[str],
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        """Synchronous wrapper for async RLM traversal."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside an event loop (e.g., parallel dispatcher)
                # Create a new thread to run it
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._traverse_async(query, seed_entities, graph)
                    )
                    return future.result(timeout=self.config.repl_timeout * self.config.max_repl_steps + 10)
            else:
                return loop.run_until_complete(
                    self._traverse_async(query, seed_entities, graph)
                )
        except Exception as e:
            logger.error("rlm_traversal_failed", error=str(e), falling_back=True)
            return self._fallback.traverse(query, seed_entities, graph)

    async def _traverse_async(
        self,
        query: str,
        seed_entities: list[str],
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        """Core async RLM traversal loop."""
        if not seed_entities:
            return TraversalResult(
                seed_entities=[], retrieved_triples=[],
                nodes_visited=0, traversal_depth=0, strategy=self.get_name()
            )

        repl = GraphREPL(graph, min_confidence=self.config.min_confidence_filter)
        system = RLM_SYSTEM_PROMPT.format(
            max_steps=self.config.max_repl_steps,
            min_conf=self.config.min_confidence_filter,
            max_depth=self.config.max_depth,
        )

        actual_depth = 0

        for step in range(self.config.max_repl_steps):
            steps_remaining = self.config.max_repl_steps - step
            prompt = RLM_STEP_PROMPT.format(
                query=query,
                seeds=", ".join(seed_entities),
                n_collected=len(repl.collected_triples),
                sample_triples=repl.get_state_summary(),
                steps_remaining=steps_remaining,
            )

            response = await asyncio.wait_for(
                self.llm.generate(prompt, system=system, context_label="rlm_traversal"),
                timeout=self.config.repl_timeout,
            )

            code = self._extract_code(response.content)

            if code == "DONE" or not code:
                logger.debug("rlm_done", step=step, triples=len(repl.collected_triples))
                break

            result = repl.execute(code)
            actual_depth = step + 1
            logger.debug("rlm_step", step=step, exec_result=result[:100], triples=len(repl.collected_triples))

            # Early stopping if we have enough triples
            if len(repl.collected_triples) >= self.config.max_nodes_per_step * self.config.max_depth:
                break

        return TraversalResult(
            seed_entities=seed_entities,
            retrieved_triples=repl.collected_triples,
            nodes_visited=len(repl.nodes_visited),
            traversal_depth=actual_depth,
            strategy=self.get_name(),
            metadata={"repl_steps": repl._exec_count},
        )

    @staticmethod
    def _extract_code(response: str) -> str:
        """Extract Python code block from LLM response."""
        if "DONE" in response and len(response.strip()) < 20:
            return "DONE"

        import re
        # Try fenced code blocks first
        match = re.search(r"```(?:python)?\n?(.*?)```", response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try indented blocks
        lines = response.split("\n")
        code_lines = [l for l in lines if l.startswith("    ") or l.strip().startswith("#")]
        if code_lines:
            return "\n".join(code_lines)

        # Return as-is if it looks like code
        if any(kw in response for kw in ("graph.", "collected_triples", "for ", "neighbors")):
            return response.strip()

        return ""
