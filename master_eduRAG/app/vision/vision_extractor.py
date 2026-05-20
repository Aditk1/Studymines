"""
Gemini-based vision extraction helpers for handwritten or image-based learning content.
"""

import os
from typing import Dict, Optional
import json
from app.vision.multi_provider import VisionExtractor as LocalVisionExtractor
from app.llm.utils import clean_json_response
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VisionExtractor:
    """
    Refactored VisionExtractor that prioritizes local OCR and Groq Vision.
    Gemini is now the final fallback.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize refactored vision extractor. 
        Note: API keys are handled internally by the LocalVisionExtractor from env.
        """
        self.extractor = LocalVisionExtractor()
        logger.info("VisionExtractor: Initialized with Multi-Provider Local/Cloud Strategy")

    def extract_from_image(self, image_path: str) -> Dict[str, str]:
        """
        Extract text and context using the multi-provider chain.
        
        Args:
            image_path: Path to image file.
            
        Returns:
            Dictionary with extracted text and metadata.
        """
        try:
            logger.debug(f"VisionExtractor: Processing image {image_path} via chain...")
            # Use the automated classifier in the new extractor
            result = self.extractor.extract(image_path, content_hint="auto")
            
            return {
                "extracted_text": result.get("text", ""),
                "content_type": "mixed", # Defaulting to mixed as specific classification is handled by the text downstream
                "diagram_descriptions": result.get("text") if result.get("method_used") == "Groq_Vision" else "",
                "confidence": "high" if result.get("method_used") != "Gemini_Vision" else "medium",
                "issues": f"Processed via {result.get('method_used')}"
            }
            
        except Exception as e:
            logger.error(f"Vision Extraction failed: {e}")
            return {
                "extracted_text": "",
                "content_type": "error",
                "error": str(e),
                "confidence": "low"
            }

    def extract_questions(self, image_path: str) -> Dict[str, list]:
        """
        Extract questions specifically (leveraging the text extracted).
        """
        # For simplicity in this replacement, we reuse the extraction logic
        # and let the downstream LLM handle the segmentation if needed.
        # But for compatibility, we return the structure expected.
        data = self.extract_from_image(image_path)
        return {
            "total_questions": 0,
            "questions": [],
            "raw_text": data.get("extracted_text", "")
        }


def extract_from_image(image_path: str, api_key: Optional[str] = None) -> Dict:
    """
    Convenience function for vision extraction.
    """
    extractor = VisionExtractor(api_key)
    return extractor.extract_from_image(image_path)
