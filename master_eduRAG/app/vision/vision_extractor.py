"""
Vision extraction module using Gemini Vision API.
Implements SAEOCR (Semantically Aware Educational OCR) for image content extraction.
"""

import base64
from typing import Dict, Optional
import cv2
import json
from app.config import VISION_MODEL
from app.clients import configure_gemini, get_vision_model
from app.llm.utils import clean_json_response, retry_with_backoff
from app.utils import get_logger

logger = get_logger(__name__)


class VisionExtractor:
    """Extracts text and context from images using Gemini Vision API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize vision extractor with Gemini API.
        
        Args:
            api_key: Gemini API key (or use GOOGLE_API_KEY env var).
        """
        if api_key:
            configure_gemini(api_key)
        self.model = get_vision_model()

    @retry_with_backoff(retries=5)
    def _generate_content(self, contents):
        """Helper to call Gemini Vision with retry logic."""
        return self.model.generate_content(contents)

    def extract_from_image(self, image_path: str) -> Dict[str, str]:
        """
        Extract text and context from image using Gemini Vision.
        
        Args:
            image_path: Path to image file.
            
        Returns:
            Dictionary with extracted text and metadata.
        """
        try:
            # Read and encode image
            image_data = self._read_image_as_base64(image_path)
            
            # Gemini vision prompt for educational content
            prompt = """
You are an educational OCR system analyzing student-generated content.

Analyze this educational image and:
1. Extract ALL visible text, preserving reading order and structure (Q1, Q2, bullets, etc.)
2. Identify the content type: 'question_paper', 'notes', 'diagram', 'mixed', or 'other'
3. Describe any diagrams, graphs, or visual elements in natural language
4. Provide a confidence indicator (high/medium/low) for extraction quality
5. Note any issues (low quality, handwriting, unclear areas)

Respond in JSON format:
{
    "extracted_text": "Full extracted text with structure preserved",
    "content_type": "question_paper|notes|diagram|mixed|other",
    "diagram_descriptions": "Description of visual elements if any",
    "confidence": "high|medium|low",
    "issues": "Any quality or legibility issues noted"
}
"""
            
            logger.debug(f"Sending request to Gemini Vision (data length: {len(image_data)})")
            response = self._generate_content([
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                },
                prompt
            ])
            logger.debug(f"Response received from Gemini.")
            
            # Parse response
            result = clean_json_response(response.text)
            return result
            
        except Exception as e:
            return {
                "extracted_text": "",
                "content_type": "error",
                "error": str(e),
                "confidence": "low"
            }

    def _read_image_as_base64(self, image_path: str) -> str:
        """
        Read image and encode as base64 for API.
        
        Args:
            image_path: Path to image.
            
        Returns:
            Base64 encoded image data.
        """
        with open(image_path, "rb") as image_file:
            return base64.standard_b64encode(image_file.read()).decode("utf-8")

    def extract_questions(self, image_path: str) -> Dict[str, list]:
        """
        Extract and segment questions from a question paper image.
        
        Args:
            image_path: Path to question paper image.
            
        Returns:
            Dictionary with segmented questions.
        """
        try:
            image_data = self._read_image_as_base64(image_path)
            
            prompt = """
This is a question paper or exam. Extract and segment all questions.

For each question, provide:
- Question number (Q1, Q2, etc.)
- Question text
- Question type (multiple_choice, short_answer, essay, etc.)
- Difficulty if indicated (easy/medium/hard)

Respond in JSON format:
{
    "total_questions": number,
    "questions": [
        {
            "number": "Q1",
            "text": "Question text",
            "type": "multiple_choice|short_answer|essay|etc",
            "difficulty": "easy|medium|hard|unknown"
        }
    ]
}
"""
            
            response = self._generate_content([
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                },
                prompt
            ])
            
            return clean_json_response(response.text)
        except Exception as e:
            return {
                "total_questions": 0,
                "questions": [],
                "error": str(e)
            }


def extract_from_image(image_path: str, api_key: Optional[str] = None) -> Dict:
    """
    Convenience function for vision extraction.
    
    Args:
        image_path: Path to image.
        api_key: Optional Gemini API key.
        
    Returns:
        Extraction result.
    """
    extractor = VisionExtractor(api_key)
    return extractor.extract_from_image(image_path)
