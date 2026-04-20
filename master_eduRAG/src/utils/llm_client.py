"""
Unified async LLM client.
Supports Ollama (local), OpenAI, and Anthropic backends.
All calls are async-compatible for use in parallel traversal.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from src.utils.config import LLMConfig
from src.utils.logger import get_logger

logger = get_logger("llm_client")


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_seconds: float = 0.0
    model: str = ""


@dataclass
class CostTracker:
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_calls: int = 0
    total_latency: float = 0.0
    records: list[dict[str, Any]] = field(default_factory=list)

    def record(self, response: LLMResponse, context: str = "") -> None:
        self.total_prompt_tokens += response.prompt_tokens
        self.total_completion_tokens += response.completion_tokens
        self.total_calls += 1
        self.total_latency += response.latency_seconds
        self.records.append({
            "context": context,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "latency": response.latency_seconds,
        })

    def summary(self) -> dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "avg_latency": self.total_latency / max(self.total_calls, 1),
            "total_latency": self.total_latency,
        }


class LLMClient:
    """
    Unified LLM client. Instantiate once, call generate() everywhere.

    Example:
        client = LLMClient(config.llm)
        response = await client.generate("Explain backpropagation.")
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.cost_tracker = CostTracker()
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        provider = self.config.provider
        if provider == "ollama":
            try:
                import ollama  # type: ignore
                self._client = ollama
            except ImportError:
                logger.warning("ollama_not_installed", msg="Install with: pip install ollama")
        elif provider == "groq":
            try:
                import os
                from openai import AsyncOpenAI  # type: ignore
                self._client = AsyncOpenAI(
                    api_key=os.getenv("GROQ_API_KEY"),
                    base_url=self.config.groq_base_url,
                )
            except ImportError:
                logger.warning("openai_not_installed", msg="Install with: pip install openai")
        elif provider == "openai":
            try:
                from openai import AsyncOpenAI  # type: ignore
                self._client = AsyncOpenAI()
            except ImportError:
                logger.warning("openai_not_installed", msg="Install with: pip install openai")
        elif provider == "anthropic":
            try:
                import anthropic  # type: ignore
                self._client = anthropic.AsyncAnthropic()
            except ImportError:
                logger.warning("anthropic_not_installed", msg="Install with: pip install anthropic")
        elif provider == "gemini":
            try:
                import google.generativeai as genai
                import os
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self._client = genai
            except ImportError:
                logger.warning("gemini_not_installed", msg="Install with: pip install google-generativeai")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        context_label: str = "",
    ) -> LLMResponse:
        """
        Generate a completion. Falls back gracefully.

        Args:
            prompt: User message.
            system: Optional system prompt override.
            context_label: Label for cost tracking records.

        Returns:
            LLMResponse with content and token counts.
        """
        t0 = time.perf_counter()
        try:
            response = await self._dispatch(prompt, system)
        except Exception as exc:
            logger.error("llm_call_failed", error=str(exc), provider=self.config.provider)
            response = LLMResponse(content="[LLM ERROR]", latency_seconds=time.perf_counter() - t0)
        response.latency_seconds = time.perf_counter() - t0
        self.cost_tracker.record(response, context=context_label)
        return response

    async def _dispatch(self, prompt: str, system: str | None) -> LLMResponse:
        provider = self.config.provider
        sys_msg = system or self.config.__dict__.get("system_prompt", "You are a helpful assistant.")

        if provider == "ollama":
            return await self._call_ollama(prompt, sys_msg)
        elif provider == "groq":
            return await self._call_groq(prompt, sys_msg)
        elif provider == "openai":
            return await self._call_openai(prompt, sys_msg)
        elif provider == "anthropic":
            return await self._call_anthropic(prompt, sys_msg)
        elif provider == "gemini":
            return await self._call_gemini(prompt, sys_msg)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _call_gemini(self, prompt: str, system: str) -> LLMResponse:
        """Call Gemini via loop.run_in_executor for async compatibility."""
        model_name = self.config.model
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
            
        model = self._client.GenerativeModel(model_name)
        
        def _sync_call():
            return model.generate_content(f"SYSTEM: {system}\n\nUSER: {prompt}")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_call)
        
        content = result.text if hasattr(result, "text") else str(result)
        return LLMResponse(
            content=content,
            prompt_tokens=len(prompt.split()), # Rough estimation as Gemini doesn't always return counts
            completion_tokens=len(content.split()),
            model=model_name,
        )

    async def _call_ollama(self, prompt: str, system: str) -> LLMResponse:
        """Call Ollama via its async interface (run sync in executor)."""
        import ollama  # type: ignore

        def _sync_call() -> Any:
            return ollama.chat(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_call)
        content = result["message"]["content"]
        usage = result.get("usage", {})
        return LLMResponse(
            content=content,
            prompt_tokens=usage.get("prompt_tokens", len(prompt.split())),
            completion_tokens=usage.get("completion_tokens", len(content.split())),
            model=self.config.model,
        )

    async def _call_groq(self, prompt: str, system: str) -> LLMResponse:
        from openai import AsyncOpenAI  # type: ignore

        client: AsyncOpenAI = self._client
        result = await client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        msg = result.choices[0].message.content or ""
        usage = result.usage
        return LLMResponse(
            content=msg,
            prompt_tokens=usage.prompt_tokens if usage else len(prompt.split()),
            completion_tokens=usage.completion_tokens if usage else len(msg.split()),
            model=self.config.model,
        )

    async def _call_openai(self, prompt: str, system: str) -> LLMResponse:
        from openai import AsyncOpenAI  # type: ignore

        client: AsyncOpenAI = self._client
        result = await client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        msg = result.choices[0].message.content or ""
        usage = result.usage
        return LLMResponse(
            content=msg,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            model=self.config.openai_model,
        )

    async def _call_anthropic(self, prompt: str, system: str) -> LLMResponse:
        import anthropic  # type: ignore

        client: anthropic.AsyncAnthropic = self._client
        result = await client.messages.create(
            model=self.config.anthropic_model,
            max_tokens=self.config.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        content = result.content[0].text if result.content else ""
        usage = result.usage
        return LLMResponse(
            content=content,
            prompt_tokens=usage.input_tokens if usage else 0,
            completion_tokens=usage.output_tokens if usage else 0,
            model=self.config.anthropic_model,
        )

    def generate_sync(self, prompt: str, system: str | None = None, context_label: str = "") -> LLMResponse:
        """Synchronous wrapper for non-async contexts."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.generate(prompt, system, context_label))
                    return future.result()
            else:
                return loop.run_until_complete(self.generate(prompt, system, context_label))
        except Exception:
            return asyncio.run(self.generate(prompt, system, context_label))
