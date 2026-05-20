"""
Run a smoke test against PDF ingestion and package generation.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.parsers.document_parser import parse_document
from app.preprocessing import preprocess_text
from app.segregation import segregate_content
from app.chunking import chunk_and_process

async def run_test(file_path: str):
    print(f"🚀 Processing: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    try:
        # 1. Parse
        print("📝 Parsing document...")
        parsed = parse_document(file_path)
        text = parsed["text"]
        print(f"✅ Extracted {len(text)} characters.")

        # 2. Preprocess
        print("🧹 Preprocessing text...")
        clean_text = preprocess_text(text)

        # 3. Segregate
        print("🏷️ Segregating content...")
        segregation = segregate_content(clean_text, file_name=os.path.basename(file_path))
        print(f"✅ Subject: {segregation.get('subject')}, Topic: {segregation.get('topic')}")

        # 4. Process (LLM + RAG)
        print("🧠 Generating Study Package & RAG Enrichment (using Gemini with fallback to Groq)...")
        result = await chunk_and_process(
            clean_text, 
            student_level="undergraduate",
            subject=segregation.get("subject"),
            topic=segregation.get("topic"),
            source_name=os.path.basename(file_path)
        )

        study_package = result["package"]
        stats = result["stats"]

        print("\n" + "="*50)
        print("💎 STUDY PACKAGE GENERATED")
        print("="*50)
        
        # Display Summary
        summary = study_package.get("summary", {})
        print(f"\nTitle: {summary.get('title', 'N/A')}")
        print(f"Content: {summary.get('content', 'N/A')[:500]}...")
        
        # Display Concepts
        print(f"\nConcepts Found: {len(study_package.get('concepts', []))}")
        for concept in study_package.get("concepts", [])[:3]:
            print(f"- {concept.get('name')}: {concept.get('definition')[:100]}...")
            
        # Display RAG Stats
        print(f"\nRAG Stats: {stats.get('nodes_count', 0)} nodes, {stats.get('edges_count', 0)} edges extracted.")
        print("="*50)

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    pdf_path = project_root / "tests" / "fixtures" / "HTML_CSS_Complete_Guide.pdf"
    asyncio.run(run_test(str(pdf_path)))
