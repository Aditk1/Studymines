"""
Multi-stage document extraction fallback pipeline for heterogeneous file formats.
"""

import logging
import fitz  # PyMuPDF
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExtractionFailedError(Exception):
    """Define the ExtractionFailedError data structure or service used by this module."""
    pass

class DocumentExtractor:
    """
    Local document extraction logic integrating PyMuPDF, Marker, and Docling.
    Used as the primary extraction layer before hitting vision APIs.
    """
    def __init__(self):
        pass
        
    def detect_type(self, file_path: str) -> str:
        """
        Probes the first page of a PDF using PyMuPDF to heuristically
        determine the structure and type of document.
        """
        try:
            doc = fitz.open(file_path)
            if doc.page_count == 0:
                return "scanned"
            
            page = doc[0]
            text = page.get_text()
            
            # Text density check
            if len(text.strip()) < 50:
                 return "scanned"
                 
            image_count = sum([len(doc.get_page_images(i)) for i in range(doc.page_count)])
            image_ratio = image_count / max(doc.page_count, 1)
            
            # Simple heuristic differentiation
            if image_ratio > 2.0 or "complex" in file_path.lower():
                 return "complex" # Best handled by Docling
            elif doc.page_count > 10:
                 return "structured" # Best handled by Marker
            else:
                 return "native" # Best handled locally by PyMuPDF
                 
        except Exception as e:
            logger.error(f"Error classifying document type for {file_path}: {e}")
            return "scanned"

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Routes the file to the optimal extraction tool based on its profile.
        """
        doc_type = self.detect_type(file_path)
        logger.info(f"[Extractor] Classified '{file_path}' as '{doc_type}'")
        
        result = {"text": "", "markdown": "", "metadata": {"type": doc_type}, "method_used": ""}
        
        if doc_type == "scanned":
            result["method_used"] = "vision_routing_needed"
            return result
             
        if doc_type == "native":
            try:
                text = ""
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text() + "\n\n"
                result["text"] = text
                result["markdown"] = text
                result["method_used"] = "PyMuPDF"
            except Exception as e:
                raise ExtractionFailedError(f"Native PyMuPDF extraction failed: {e}")
             
        elif doc_type == "structured":
            logger.info("[Extractor] Engaging Marker for structured PDF...")
            try:
                from marker.converters.pdf import PdfConverter
                from marker.models import create_model_dict
                from marker.config.parser import ConfigParser
                
                converter = PdfConverter(artifact_dict=create_model_dict(), config=ConfigParser({}).generate_config_dict())
                rendered = converter(file_path)
                result["text"] = rendered.markdown
                result["markdown"] = rendered.markdown
                result["method_used"] = "Marker"
            except Exception as e:
                logger.warning(f"[Extractor] Marker failed ({e}), falling back to PyMuPDF")
                doc = fitz.open(file_path)
                result["text"] = "\n\n".join([p.get_text() for p in doc])
                result["markdown"] = result["text"]
                result["method_used"] = "PyMuPDF_Fallback"
                 
        elif doc_type == "complex":
            logger.info("[Extractor] Engaging Docling for complex PDF...")
            try:
                from docling.document_converter import DocumentConverter
                converter = DocumentConverter()
                conv_res = converter.convert(file_path)
                markdown_output = conv_res.document.export_to_markdown()
                result["markdown"] = markdown_output
                result["text"] = markdown_output
                result["method_used"] = "Docling"
            except Exception as e:
                logger.warning(f"[Extractor] Docling failed ({e}), falling back to PyMuPDF")
                doc = fitz.open(file_path)
                result["text"] = "\n\n".join([p.get_text() for p in doc])
                result["markdown"] = result["text"]
                result["method_used"] = "PyMuPDF_Fallback"
                 
        return result
