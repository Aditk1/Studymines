"""
High-level StudyMines orchestration for document parsing and package generation.
"""

import os
import logging
from typing import Dict, Any
import fitz  # PyMuPDF

from app.llm.multi_provider import LLMClient
from app.parsers.multi_stage import DocumentExtractor
from app.vision.multi_provider import VisionExtractor

logger = logging.getLogger(__name__)

class StudyMinesPipeline:
    """
    Top-level orchestrator interfacing Local Extraction, Vision Pipelines, and multi-provider LLMs.
    Integrated into the main app structure to handle high-performance, cost-effective ingestion.
    """
    
    def __init__(self):
        self.llm = LLMClient()
        self.doc_extractor = DocumentExtractor()
        self.vision_extractor = VisionExtractor()
        
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Ingests a document, processing natively or rendering to vision based on its needs.
        """
        logger.info(f"Starting pipeline processing for: {file_path}")
        try:
            doc_result = self.doc_extractor.extract(file_path)
            
            if doc_result.get("method_used") == "vision_routing_needed":
                logger.info("Scanned document detected. Transcribing via VisionExtractor per page.")
                doc = fitz.open(file_path)
                full_text = ""
                methods = set()
                
                for i in range(len(doc)):
                    page = doc[i]
                    pix = page.get_pixmap(dpi=150)
                    temp_img_path = f"temp_cv_page_{i}.png"
                    pix.save(temp_img_path)
                    
                    vision_res = self.vision_extractor.extract(temp_img_path, content_hint="auto")
                    full_text += vision_res.get("text", "") + "\n\n"
                    methods.add(vision_res.get("method_used", "Unknown"))
                    
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                
                doc_result["text"] = full_text
                doc_result["markdown"] = full_text
                doc_result["method_used"] = f"VisionExtractor({', '.join(methods)})"
            
            return doc_result
        except Exception as e:
            logger.error(f"Pipeline process_document failed for {file_path}: {e}")
            raise
            
    def generate_summary(self, text: str) -> str:
        """Generates an educational summary."""
        prompt = f"Please provide a comprehensive summary for the following educational text:\n\n{text}"
        system = "You are an expert educational tutor. Deliver concise and highly accurate summaries."
        return self.llm.complete(prompt, system=system)
        
    def generate_qa(self, text: str, num_questions: int = 5) -> str:
        """Generates exam-style questions."""
        prompt = f"Generate {num_questions} high-quality questions and answers based on this text:\n\n{text}"
        system = "You are an expert exam setter. Return only the Q&A pairs."
        return self.llm.complete(prompt, system=system)
        
    def tag_concepts(self, text: str) -> str:
        """Tags core concepts from the educational content."""
        prompt = f"Extract a comma-separated list of the 10 most important core concepts from this text:\n\n{text}"
        system = "You are an educational metadata tagger. Output only the comma-separated tags."
        return self.llm.complete(prompt, system=system)
