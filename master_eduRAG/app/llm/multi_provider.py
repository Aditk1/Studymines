"""
Multi-provider LLM client with ordered fallback across configured cloud/local providers.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from groq import Groq
from openai import OpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AllProvidersExhaustedError(Exception):
    """Raised when all LLM providers in the fallback chain have failed."""
    pass


class LLMClient:
    """
    Multi-provider LLM Client holding connections to Groq, Cerebras, OpenRouter, and Gemini.
    Provides intelligent fallback and exponential backoff to handle rate-limits on free tiers.
    """
    
    def __init__(self):
        # Groq Client (Primary)
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        
        # Cerebras Client (Fallback 1) - using official SDK
        try:
            from cerebras.cloud.sdk import Cerebras
            self.cerebras_client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY", ""))
        except ImportError:
            logger.warning("cerebras-cloud-sdk not installed, falling back to OpenAI proxy format")
            self.cerebras_client = OpenAI(
                base_url="https://api.cerebras.ai/v1",
                api_key=os.getenv("CEREBRAS_API_KEY", "")
            )
        
        # Gemini Client (Fallback 2)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        
        # OpenRouter Client (Fallback 3)
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY", "")
        )

        self.providers = [
            {"name": "Groq", "model": "llama-3.3-70b-versatile", "func": self._call_groq},
            {"name": "Cerebras", "model": "llama3.1-8b", "func": self._call_cerebras},
            {"name": "Gemini", "model": "gemini-2.0-flash", "func": self._call_gemini},
            {"name": "OpenRouter", "model": "deepseek/deepseek-chat:free", "func": self._call_openrouter},
        ]

    def _call_groq(self, prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def _call_cerebras(self, prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self.cerebras_client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def _call_gemini(self, prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
        content = prompt
        if system:
            content = f"System Instruction: {system}\n\nUser Request: {prompt}"
        response = self.gemini_model.generate_content(content)
        return response.text

    def _call_openrouter(self, prompt: str, system: Optional[str], model: str, max_tokens: int) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = self.openrouter_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def complete(self, prompt: str, system: Optional[str] = None, max_tokens: int = 2048) -> str:
        """Completes the prompt by systematically iterating through the providers on failures."""
        backoff_times = [0.5, 1.0, 2.0]
        exceptions_caught = []

        for provider in self.providers:
            name = provider["name"]
            model = provider["model"]
            caller = provider["func"]
            
            retries = 0
            while retries <= 2:
                start_time = time.time()
                try:
                    logger.debug(f"[LLM] Attempting {name} ({model}) - Try {retries+1}")
                    result = caller(prompt, system, model, max_tokens)
                    latency = time.time() - start_time
                    logger.info(f"[LLM] Success with {name} in {latency:.2f}s")
                    return result
                except Exception as e:
                    latency = time.time() - start_time
                    logger.warning(f"[LLM] {name} failed on try {retries+1} after {latency:.2f}s. Error: {e}")
                    
                    if retries < 2:
                        sleep_time = backoff_times[retries]
                        logger.debug(f"[LLM] Sleeping for {sleep_time}s before next try...")
                        time.sleep(sleep_time)
                        retries += 1
                    else:
                        exceptions_caught.append(f"{name}: {str(e)}")
                        break 

        error_msg = " | ".join(exceptions_caught)
        logger.error(f"[LLM] All providers exhausted: {error_msg}")
        raise AllProvidersExhaustedError(f"All LLM providers exhausted. Errors: {error_msg}")
