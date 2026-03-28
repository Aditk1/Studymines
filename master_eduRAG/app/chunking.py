"""
Document chunking and map-reduce summarisation for long documents.
Integrates with the RAG Bridge for graph enrichment.
"""

import json
from typing import Dict, List, Optional
import google.generativeai as genai
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, DEFAULT_MODEL
from app.llm.utils import clean_json_response, retry_with_backoff


class DocumentChunker:
    """Splits long documents into manageable chunks for LLM processing."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def needs_chunking(self, text: str) -> bool:
        return self.estimate_tokens(text) > self.chunk_size

    def chunk_text(self, text: str) -> List[str]:
        if not self.needs_chunking(text):
            return [text]

        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > char_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                overlap_text = current_chunk[-char_overlap:] if len(current_chunk) > char_overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                current_chunk = (current_chunk + "\n\n" + paragraph) if current_chunk else paragraph

        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks

    def needs_map_reduce(self, chunks: List[str]) -> bool:
        return len(chunks) > 5


class MapReduceProcessor:
    """Map-Reduce strategy for long-document study-package generation."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    @retry_with_backoff(retries=5)
    def _generate_content(self, prompt: str):
        return self.model.generate_content(prompt)

    def map_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        prompt = f"""You are summarizing part {chunk_index + 1} of {total_chunks} of an educational document.
Extract key information, concepts, and important details.
Preserve any specific facts, definitions, formulas, or examples.

Text chunk:
{chunk}

Provide a comprehensive summary. Respond with only the summary text."""
        try:
            return self._generate_content(prompt).text
        except Exception:
            return chunk[:2000]

    def reduce_summaries(self, chunk_summaries, student_level="undergraduate", subject=None, topic=None):
        combined = "\n\n---\n\n".join(
            f"[Section {i+1}]\n{s}" for i, s in enumerate(chunk_summaries)
        )
        context = ""
        if subject:
            context += f"Subject: {subject}\n"
        if topic:
            context += f"Topic: {topic}\n"

        prompt = f"""You are an expert educational content specialist. Generate study materials from these combined section summaries.

{context}Student Level: {student_level}

Combined Section Summaries:
{combined}

Generate the FOLLOWING in JSON format:
1. LEVELED SUMMARY adapted to {student_level}.
2. KEY CONCEPTS (5+).
3. FLASHCARDS (6+) with difficulty tags.
4. EXAM QUESTIONS (4+) covering Bloom's taxonomy.

Respond ONLY with valid JSON:
{{
    "summary": {{"title": "...", "content": "...", "length_level": "brief|moderate|detailed"}},
    "concepts": [{{"name":"...","definition":"...","importance":"high|medium|low"}}],
    "flashcards": [{{"question":"...","answer":"...","difficulty":"easy|medium|hard","tags":["..."]}}],
    "questions": [{{"question":"...","question_type":"recall|understand|apply|analyze","difficulty":"easy|medium|hard","model_answer":"...","explanation":"..."}}]
}}"""

        try:
            result = clean_json_response(self._generate_content(prompt).text)
            return {
                "success": True, "data": result, "student_level": student_level,
                "processing_method": "map_reduce", "chunks_processed": len(chunk_summaries),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "data": {}, "processing_method": "map_reduce"}

    def process(self, chunks, student_level="undergraduate", subject=None, topic=None):
        print(f"  MAP phase: summarizing {len(chunks)} chunks...")
        summaries = []
        for i, chunk in enumerate(chunks):
            summaries.append(self.map_chunk(chunk, i, len(chunks)))
            print(f"    Chunk {i+1}/{len(chunks)} summarized")
        print(f"  REDUCE phase: generating study package from {len(summaries)} summaries...")
        return self.reduce_summaries(summaries, student_level, subject, topic)


async def chunk_and_process(
    text: str,
    student_level: str = "undergraduate",
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    api_key: Optional[str] = None,
    source_name: str = "document_upload",
) -> Dict:
    """
    Chunk text → generate study package → enrich via RLM-GraphRAG bridge.
    """
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(text)

    if chunker.needs_map_reduce(chunks):
        print(f"Document split into {len(chunks)} chunks — using map-reduce strategy")
        study_package = MapReduceProcessor(api_key).process(chunks, student_level, subject, topic)
    else:
        from app.llm.epf_generator import generate_study_package
        combined = "\n\n".join(chunks)
        print(f"Document has {len(chunks)} chunk(s) — using direct EPF generation")
        study_package = generate_study_package(combined, student_level, subject, topic, api_key)

    # ── RAG Enrichment (Milestone 1 & 2) ──
    try:
        from app.bridge import process_with_rag
        print("💡 Enriching study package with RLM-GraphRAG Cognitive Core...")
        pkg, stats = await process_with_rag(text, source_name, study_package)
        return {"package": pkg, "stats": stats}
    except Exception as e:
        print(f"⚠ RAG enrichment skipped: {e}")
        return {"package": study_package, "stats": {}}
