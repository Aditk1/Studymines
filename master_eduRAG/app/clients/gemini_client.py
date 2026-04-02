"""
Centralized Gemini API client.
Provides singleton-like access to Gemini API with configuration management.
"""

import os
from typing import Optional
import google.generativeai as genai
from app.config import DEFAULT_MODEL, VISION_MODEL


class GeminiClient:
    """Singleton-like Gemini client manager."""
    
    _instance = None
    _initialized = False
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client with API key."""
        if api_key:
            genai.configure(api_key=api_key)
        elif not self._initialized:
            # If no api_key provided, genai will use GOOGLE_API_KEY env var
            pass
        GeminiClient._initialized = True
    
    @classmethod
    def get_client(cls, api_key: Optional[str] = None) -> "GeminiClient":
        """Get or create Gemini client instance."""
        if cls._instance is None:
            cls._instance = cls(api_key)
        return cls._instance
    
    def get_model(self, model_name: Optional[str] = None) -> genai.GenerativeModel:
        """
        Get a Gemini model instance.
        
        Args:
            model_name: Model to use. Defaults to DEFAULT_MODEL from config.
            
        Returns:
            genai.GenerativeModel instance
        """
        if not model_name:
            model_name = DEFAULT_MODEL
        
        # Ensure model name has "models/" prefix
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        
        return genai.GenerativeModel(model_name)
    
    def get_vision_model(self, model_name: Optional[str] = None) -> genai.GenerativeModel:
        """
        Get a Gemini Vision model instance.
        
        Args:
            model_name: Vision model to use. Defaults to VISION_MODEL from config.
            
        Returns:
            genai.GenerativeModel instance for vision tasks
        """
        if not model_name:
            model_name = VISION_MODEL
        
        # Ensure model name has "models/" prefix
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        
        return genai.GenerativeModel(model_name)


# Module-level convenience functions for backward compatibility
_client = None

def configure_gemini(api_key: Optional[str] = None):
    """Configure Gemini API with optional API key."""
    global _client
    _client = GeminiClient.get_client(api_key)


def get_model(model_name: Optional[str] = None) -> genai.GenerativeModel:
    """Get a Gemini model instance."""
    global _client
    if _client is None:
        _client = GeminiClient.get_client()
    return _client.get_model(model_name)


def get_vision_model(model_name: Optional[str] = None) -> genai.GenerativeModel:
    """Get a Gemini Vision model instance."""
    global _client
    if _client is None:
        _client = GeminiClient.get_client()
    return _client.get_vision_model(model_name)
