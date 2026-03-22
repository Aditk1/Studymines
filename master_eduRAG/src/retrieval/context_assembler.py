"""
Context Assembly and Answer Generation.

ContextAssembler: deduplicates and ranks retrieved triples into a text context.
AnswerGenerator: calls the LLM with assembled context to produce a final answer.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import numpy as np

from src.graph.knowledge_graph import Triple
from src.traversal.base import TraversalResult
from src.utils.config import AnswerGenerationConfig, RetrievalConfig
from src.utils.llm_client import LLMClient, LLMResponse
from src.utils.logger import get_logger
from src.utils.vector_store import EmbeddingModel

logger = get_logger("retrieval")


class ContextAssembler:
    """
    Assembles a text context from retrieved triples.
    Deduplicates by semantic similarity and enforces a token budget.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        config: RetrievalConfig,
    ) -> None:
        self.embedding_model = embedding_model
        self.config = config

    def assemble(self, result: TraversalResult) -> str:
        """
        Build a context string from traversal results.

        Args:
            result: TraversalResult with retrieved triples.

        Returns:
            Context string ready for LLM consumption.
        """
        triples = result.retrieved_triples
        if not triples:
            return ""

        # Sort by confidence descending
        triples = sorted(triples, key=lambda t: t.confidence, reverse=True)

        # Deduplicate by text
        unique = self._deduplicate(triples)

        # Enforce token budget (approximate: 1 token ≈ 0.75 words)
        word_budget = int(self.config.context_max_tokens * 0.75)
        context_lines: list[str] = []
        word_count = 0

        for triple in unique:
            line = f"({triple.subject}, {triple.relation}, {triple.obj})"
            line_words = len(line.split())
            if word_count + line_words > word_budget:
                break
            context_lines.append(line)
            word_count += line_words

        context = "\n".join(context_lines)
        logger.debug(
            "context_assembled",
            num_triples=len(context_lines),
            approx_tokens=word_count,
        )
        return context

    def _deduplicate(self, triples: list[Triple]) -> list[Triple]:
        """Remove near-duplicate triples using text similarity."""
        if len(triples) <= 1:
            return triples

        texts = [t.to_text() for t in triples]
        try:
            embeddings = self.embedding_model.encode(texts, normalize=True)
            unique_indices: list[int] = [0]

            for i in range(1, len(triples)):
                is_dup = False
                for j in unique_indices:
                    sim = float(np.dot(embeddings[i], embeddings[j]))
                    if sim >= self.config.dedup_similarity_threshold:
                        is_dup = True
                        break
                if not is_dup:
                    unique_indices.append(i)

            return [triples[i] for i in unique_indices]
        except Exception:
            # Fallback: simple text dedup
            seen: set[str] = set()
            unique: list[Triple] = []
            for t in triples:
                key = t.to_text()
                if key not in seen:
                    seen.add(key)
                    unique.append(t)
            return unique


@dataclass
class QAResult:
    """Complete result for one query."""
    query: str
    answer: str
    context: str
    seed_entities: list[str]
    nodes_visited: int
    traversal_depth: int
    traversal_strategy: str
    llm_response: LLMResponse
    metadata: dict = None  # type: ignore

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


ANSWER_PROMPT_TEMPLATE = """Context (knowledge graph triples):
{context}

Question: {query}

Instructions: Answer the question using ONLY the context above.
If the answer is not in the context, respond with exactly: "Not found."
Be concise and direct. For factual questions, give the answer without explanation."""


class AnswerGenerator:
    """
    Generates answers by combining retrieved context with an LLM call.
    """

    def __init__(self, config: AnswerGenerationConfig, llm_client: LLMClient) -> None:
        self.config = config
        self.llm = llm_client

    async def generate(self, query: str, context: str) -> LLMResponse:
        """Generate an answer given query and context."""
        if not context.strip():
            prompt = f"Question: {query}\n\nNo relevant context was found. Answer: Not found."
        else:
            prompt = ANSWER_PROMPT_TEMPLATE.format(context=context, query=query)

        return await self.llm.generate(
            prompt,
            system=self.config.system_prompt,
            context_label="answer_generation",
        )

    def generate_sync(self, query: str, context: str) -> LLMResponse:
        return asyncio.run(self.generate(query, context))
