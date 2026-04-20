"""
Centralized Groq API client.
Provides access to Groq-hosted Llama models for online preprocessing (vision/OCR)
and text generation. Replaces Gemini for free, unlimited API access.
"""

import os
import base64
from typing import Optional
from app.utils import get_logger

logger = get_logger(__name__)

# Default models
DEFAULT_GROQ_TEXT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROQ_VISION_MODEL = "llama-3.2-11b-vision-preview"


class GroqClient:
    """Singleton-like Groq client manager."""

    _instance = None

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq client with API key."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. Groq calls will fail.")
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        except ImportError:
            logger.warning("groq package not installed. Run: pip install groq")
            self._client = None

    @classmethod
    def get_client(cls, api_key: Optional[str] = None) -> "GroqClient":
        """Get or create Groq client singleton instance."""
        if cls._instance is None:
            cls._instance = cls(api_key)
        return cls._instance

    def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate a text response using Groq.

        Args:
            prompt: User prompt.
            model: Optional model override. Defaults to DEFAULT_GROQ_TEXT_MODEL.

        Returns:
            Generated text string.
        """
        if not self._client:
            raise RuntimeError("Groq client not initialized. Check GROQ_API_KEY.")

        model_name = model or DEFAULT_GROQ_TEXT_MODEL
        try:
            response = self._client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq text generation failed: {e}")
            raise

    def generate_vision(self, image_path: str, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate a response from an image using Groq Vision (Llama 3.2 Vision).

        Args:
            image_path: Path to the image file.
            prompt: Text prompt accompanying the image.
            model: Optional model override. Defaults to DEFAULT_GROQ_VISION_MODEL.

        Returns:
            Generated text string from the vision model.
        """
        if not self._client:
            raise RuntimeError("Groq client not initialized. Check GROQ_API_KEY.")

        model_name = model or DEFAULT_GROQ_VISION_MODEL

        # Read and encode image to base64
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Detect MIME type from extension
        ext = image_path.rsplit(".", 1)[-1].lower()
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
        mime_type = mime_map.get(ext, "image/jpeg")

        try:
            response = self._client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq vision generation failed: {e}")
            raise


# ---------------------------------------------------------------------------
# Module-level convenience functions (backward-compatible interface)
# ---------------------------------------------------------------------------

_client: Optional[GroqClient] = None


def configure_groq(api_key: Optional[str] = None):
    """Configure Groq client with optional API key."""
    global _client
    _client = GroqClient.get_client(api_key)


def get_groq_client() -> GroqClient:
    """Get the module-level Groq client, initializing if needed."""
    global _client
    if _client is None:
        _client = GroqClient.get_client()
    return _client


def groq_generate_text(prompt: str, model: Optional[str] = None) -> str:
    """Convenience function: generate text via Groq."""
    return get_groq_client().generate_text(prompt, model)


def groq_generate_vision(image_path: str, prompt: str, model: Optional[str] = None) -> str:
    """Convenience function: analyze image via Groq Vision."""
    return get_groq_client().generate_vision(image_path, prompt, model)
