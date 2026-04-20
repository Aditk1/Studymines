"""
Ollama client for local reasoning and generation.
Provides a standard interface for non-stop, private LLM execution.
"""

import requests
import json
from typing import Optional, Dict, Any
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OllamaClient:
    """Synchronous client for Ollama API."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.generate_url = f"{self.base_url}/api/generate"

    def generate(self, prompt: str, model: str = OLLAMA_MODEL, options: Optional[Dict] = None) -> str:
        """
        Produce a non-streaming response from Ollama.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if options:
            payload["options"] = options

        try:
            logger.debug(f"Ollama Request [model={model}]: {prompt[:50]}...")
            response = requests.post(self.generate_url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Ollama error: {str(e)}")

# Singleton instance
_client = OllamaClient()

def ollama_generate(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Convenience helper for Ollama generation."""
    return _client.generate(prompt, model=model)
