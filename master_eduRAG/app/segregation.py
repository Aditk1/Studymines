"""
Subject / topic segregation module.
Auto-classifies content via Gemini or accepts manual labels.
"""

import json
from typing import Dict, Optional
from app.clients import groq_generate_text, get_model, configure_gemini
from app.llm.utils import clean_json_response
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ContentSegregator:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize ContentSegregator with Gemini primary and Groq fallback."""
        if api_key:
            configure_gemini(api_key)
        
        try:
            self.model = get_model()
            logger.info("ContentSegregator: Initialized with Gemini")
        except Exception as e:
            logger.error(f"ContentSegregator: Gemini init failed: {e}")
            self.model = None

    def manual_segregate(self, subject: str, topic: str) -> Dict[str, str]:
        return {"subject": subject.strip(), "topic": topic.strip(), "method": "manual"}

    def auto_segregate(self, text: str, file_name: Optional[str] = None) -> Dict[str, str]:
        context = f"File: {file_name}\n\n" if file_name else ""
        context += f"Content Preview:\n{text[:1000]}"

        prompt = f"""You are an educational content classifier. Analyze the following and categorize it into:
1. Subject (broad, e.g. Mathematics, Biology)
2. Topic (specific, e.g. Algebra, Photosynthesis)

{context}

Respond ONLY with valid JSON:
{{
    "subject": "Subject Name",
    "topic": "Topic Name",
    "confidence": "high/medium/low"
}}"""

        # A. Try Gemini
        if self.model:
            try:
                response = self.model.generate_content(prompt)
                result = clean_json_response(response.text)
                result["method"] = "auto"
                return result
            except Exception as e:
                logger.warning(f"ContentSegregator: Gemini failed: {e}. Falling back to Groq.")

        # B. Try Groq
        try:
            response_text = groq_generate_text(prompt)
            result = clean_json_response(response_text)
            result["method"] = "auto"
            return result
        except Exception as e:
            logger.error(f"ContentSegregator: Groq fallback failed: {e}")
            return {
                "subject": "Unknown", "topic": "Unclassified",
                "confidence": "low", "method": "auto", "error": str(e),
            }

    def segregate(self, text, manual_subject=None, manual_topic=None, file_name=None):
        if manual_subject and manual_topic:
            return self.manual_segregate(manual_subject, manual_topic)
        return self.auto_segregate(text, file_name)


def segregate_content(text, manual_subject=None, manual_topic=None, file_name=None, api_key=None):
    return ContentSegregator(api_key).segregate(text, manual_subject, manual_topic, file_name)
