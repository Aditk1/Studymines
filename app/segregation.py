"""
Subject and topic segregation module for EduSum.
Categorizes uploads into subject -> topic hierarchy.
Can handle manual input or auto-analysis via Gemini.
"""

import json
from typing import Dict, Tuple, Optional
import google.generativeai as genai


class ContentSegregator:
    """Segregates educational content into subject and topic categories."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize segregator with Gemini API.
        
        Args:
            api_key: Gemini API key (or use GOOGLE_API_KEY env var).
        """
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    def manual_segregate(self, subject: str, topic: str) -> Dict[str, str]:
        """
        Accept manual subject and topic input from user.
        
        Args:
            subject: Subject name (e.g., 'Mathematics').
            topic: Topic name (e.g., 'Algebra').
            
        Returns:
            Dictionary with subject and topic.
        """
        return {
            "subject": subject.strip(),
            "topic": topic.strip(),
            "method": "manual"
        }

    def auto_segregate(self, text: str, file_name: Optional[str] = None) -> Dict[str, str]:
        """
        Auto-analyze content using Gemini to infer subject and topic.
        
        Args:
            text: Extracted text from document/image.
            file_name: Optional file name for additional context.
            
        Returns:
            Dictionary with inferred subject and topic.
        """
        # Prepare context
        context = f"File: {file_name}\n\n" if file_name else ""
        context += f"Content Preview:\n{text[:1000]}"  # First 1000 chars

        # Gemini prompt for categorization
        prompt = f"""
You are an educational content classifier. Analyze the following educational content and categorize it into:
1. Subject (broad category, e.g., Mathematics, Biology, History, Physics, Chemistry, Literature)
2. Topic (specific sub-area, e.g., under Mathematics: Algebra, Calculus, Geometry)

{context}

Respond in JSON format:
{{
    "subject": "Subject Name",
    "topic": "Topic Name",
    "confidence": "high/medium/low"
}}

Only return valid JSON, no additional text.
"""

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            result["method"] = "auto"
            return result
        except Exception as e:
            print(f"Error in auto-segregation: {e}")
            return {
                "subject": "Unknown",
                "topic": "Unclassified",
                "confidence": "low",
                "method": "auto",
                "error": str(e)
            }

    def segregate(
        self,
        text: str,
        manual_subject: Optional[str] = None,
        manual_topic: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Segregate content using manual input or auto-analysis.
        Prefers manual input if provided.
        
        Args:
            text: Extracted text.
            manual_subject: Optional manual subject input.
            manual_topic: Optional manual topic input.
            file_name: Optional file name for auto-analysis context.
            
        Returns:
            Dictionary with subject, topic, and method.
        """
        # Prefer manual input if provided
        if manual_subject and manual_topic:
            return self.manual_segregate(manual_subject, manual_topic)
        
        # Fall back to auto-analysis
        return self.auto_segregate(text, file_name)


def segregate_content(
    text: str,
    manual_subject: Optional[str] = None,
    manual_topic: Optional[str] = None,
    file_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Convenience function for content segregation.
    
    Args:
        text: Extracted text.
        manual_subject: Optional manual subject.
        manual_topic: Optional manual topic.
        file_name: Optional file name.
        api_key: Optional Gemini API key.
        
    Returns:
        Segregation result.
    """
    segregator = ContentSegregator(api_key)
    return segregator.segregate(text, manual_subject, manual_topic, file_name)
