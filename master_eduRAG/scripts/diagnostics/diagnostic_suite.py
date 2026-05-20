"""
Run a local diagnostic suite for imports, database, parsing, LLM, and RAG smoke checks.
"""


import sys
import asyncio
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def test_imports():
    print("--- [1] Testing Imports ---")
    try:
        from app.database import SessionLocal, get_db
        from app.models import User
        from app.parsers.document_parser import PDFParser
        from app.llm.epf_generator import EPFGenerator
        from app.bridge import RAGBridge
        from app.lms.risk_engine import RiskEngine
        print("[OK] All core modules imported successfully.")
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")

def test_db_connection():
    print("\n--- [2] Testing Database ---")
    from app.database import SessionLocal, init_db
    try:
        # init_db() # Don't re-init if running
        db = SessionLocal()
        user_count = db.query(User).count()
        print(f"[OK] DB Connected. User count: {user_count}")
        db.close()
    except Exception as e:
        print(f"[FAIL] DB Connection failed: {e}")

def test_pdf_parser():
    print("\n--- [3] Testing PDF Parser ---")
    from app.parsers.document_parser import PDFParser
    pdf_path = ROOT / "tests" / "fixtures" / "HTML_CSS_Complete_Guide.pdf"
    if not pdf_path.exists():
        print(f"[WARN] Test PDF not found at {pdf_path}")
        return
    try:
        parser = PDFParser()
        text = parser.extract_text(str(pdf_path))
        print(f"[OK] PDF Extracted. Length: {len(text)} chars.")
        print(f"   Snippet: {text[:100]}...")
    except Exception as e:
        print(f"[FAIL] PDF Parsing failed: {e}")

async def test_llm_generation():
    print("\n--- [4] Testing LLM Generation (Cloud/Gemini) ---")
    from app.llm.epf_generator import EPFGenerator
    try:
        gen = EPFGenerator()
        sample_text = "Photosynthesis is the process by which green plants use sunlight to synthesize nutrients."
        result = gen.generate_summary(sample_text)
        if "content" in result:
             print("[OK] Gemini/LLM Summary generated successfully.")
        else:
             print(f"[WARN] Generation returned unexpected format: {result}")
    except Exception as e:
        print(f"[FAIL] LLM Generation failed: {e}")

async def test_rag_ingestion_smoke():
    print("\n--- [5] Testing GraphRAG Ingestion (Smoke) ---")
    from app.bridge import RAGBridge
    try:
        bridge = RAGBridge()
        if not bridge.pipeline:
            print("[WARN] RAG Pipeline not initialized (Config missing or RAG_AVAILABLE=False)")
            return
        print("[OK] RAG Bridge initialized.")
        # We won't do a full Llama ingest here as it might be too slow for a diagnostic
    except Exception as e:
        print(f"[FAIL] RAG Bridge failed: {e}")

async def run_all():
    test_imports()
    test_db_connection()
    test_pdf_parser()
    await test_llm_generation()
    await test_rag_ingestion_smoke()
    print("\n--- Diagnostic Complete ---")

if __name__ == "__main__":
    from app.models import User # For local scope in test_db
    asyncio.run(run_all())
