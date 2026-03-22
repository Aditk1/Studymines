"""
Answer generation: takes assembled context and generates a final answer.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from src.utils.config import AnswerGenerationConfig
from src.utils.llm_client import LLMClient, LLMResponse
from src.utils.logger import get_logger

logger = get_logger("answer_generator")

ANSWER_PROMPT = """You are a helpful study assistant. Using the knowledge graph context provided below, please answer the student's question accurately and helpfully.

Context (knowledge graph triples):
{context}

Question: {question}

Please provide a detailed and grounded answer:
Answer:"""


@dataclass
class GeneratedAnswer:
    question: str
    answer: str
    context_used: str
    prompt_tokens: int
    completion_tokens: int
    latency_seconds: float
    model: str


class AnswerGenerator:
    """Generates answers from context using the configured LLM."""

    def __init__(self, config: AnswerGenerationConfig, llm_client: LLMClient) -> None:
        self.config = config
        self.llm = llm_client

    async def generate(self, question: str, context: str) -> GeneratedAnswer:
        """Generate answer given a question and context string."""
        prompt = ANSWER_PROMPT.format(
            context=context[:4000],
            question=question,
        )
        t0 = time.perf_counter()
        response: LLMResponse = await self.llm.generate(
            prompt,
            system=self.config.system_prompt,
            context_label="answer_generation",
        )
        latency = time.perf_counter() - t0
        return GeneratedAnswer(
            question=question,
            answer=response.content.strip(),
            context_used=context,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_seconds=latency,
            model=response.model,
        )

    def generate_sync(self, question: str, context: str) -> GeneratedAnswer:
        import asyncio
        return asyncio.run(self.generate(question, context))