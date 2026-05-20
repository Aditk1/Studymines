"""
Pre-download or warm local ML models used by parsing and GraphRAG workflows.
"""

import os
import sys

# Add the project root to sys.path so we can import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def warmup_docling():
    print("--- Warming up Docling (Layout Models) ---")
    try:
        from docling.document_converter import DocumentConverter
        # This usually triggers the download of the layout model
        converter = DocumentConverter()
        print("✓ Docling initialized successfully.")
    except Exception as e:
        print(f"✗ Docling warmup failed: {e}")

def warmup_marker():
    print("\n--- Warming up Marker (PDF Structured Models) ---")
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.config.parser import ConfigParser
        
        # This triggers model dictionary creation and checking
        print("Initializing Marker model dictionary...")
        artifact_dict = create_model_dict()
        print("Initializing Marker PDF Converter...")
        converter = PdfConverter(artifact_dict=artifact_dict, config=ConfigParser({}).generate_config_dict())
        print("✓ Marker initialized successfully.")
    except Exception as e:
        print(f"✗ Marker warmup failed: {e}")

def warmup_paddle():
    print("\n--- Warming up PaddleOCR (OCR Models) ---")
    try:
        from paddleocr import PaddleOCR
        # This will download det, rec, and cls models if not present
        ocr = PaddleOCR(use_textline_orientation=True, lang="en")
        print("✓ PaddleOCR initialized successfully.")
    except Exception as e:
        print(f"✗ PaddleOCR warmup failed: {e}")

def warmup_transformers():
    print("\n--- Warming up Transformers (TrOCR Handwritten Models) ---")
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    try:
        model_id = 'microsoft/trocr-base-handwritten'
        print(f"Downloading/Loading {model_id}...")
        processor = TrOCRProcessor.from_pretrained(model_id)
        model = VisionEncoderDecoderModel.from_pretrained(model_id)
        print("✓ TrOCR initialized successfully.")
    except Exception as e:
        print(f"✗ TrOCR warmup failed: {e}")

if __name__ == "__main__":
    print("====================================================")
    print("   master_eduRAG — AI Model Warmup Script")
    print("   (Pre-downloading necessary model weights)")
    print("====================================================")
    
    warmup_docling()
    warmup_marker()
    warmup_paddle()
    warmup_transformers()
    
    print("\n====================================================")
    print("   Warmup Complete! All models are now cached.")
    print("   You can now run the project without download delays.")
    print("====================================================")
