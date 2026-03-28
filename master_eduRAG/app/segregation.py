"""
Subject / topic segregation module.
Auto-classifies content via Gemini or accepts manual labels.
"""

import json
from typing import Dict, Optional
import google.generativeai as genai


class ContentSegregator:
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            genai.configure(api_key=api_key)
        from app.config import DEFAULT_MODEL
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

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

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            result["method"] = "auto"
            return result
        except Exception as e:
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
