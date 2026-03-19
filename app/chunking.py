"""
Document chunking and map-reduce summarization for EduSum.
Handles long documents by splitting into chunks and applying
map-reduce strategy as specified in the PRD.

PRD Requirements:
- Chunk documents exceeding 3,000 tokens using sliding window with 200-token overlap
- Apply map-reduce summarization for documents with more than 5 chunks
- Preserve section hierarchy metadata
"""

import json
from typing import Dict, List, Optional
import google.generativeai as genai
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, DEFAULT_MODEL
from app.llm.utils import clean_json_response, retry_with_backoff


class DocumentChunker:
    """Splits long documents into manageable chunks for LLM processing."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize chunker with configurable size and overlap.

        Args:
            chunk_size: Maximum tokens per chunk (default: 3000).
            chunk_overlap: Token overlap between chunks (default: 200).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text.
        Approximate: 1 token ≈ 4 characters for English text.

        Args:
            text: Input text.

        Returns:
            Estimated token count.
        """
        return len(text) // 4

    def needs_chunking(self, text: str) -> bool:
        """
        Check if text exceeds chunk size and needs splitting.

        Args:
            text: Input text.

        Returns:
            True if text needs chunking.
        """
        return self.estimate_tokens(text) > self.chunk_size

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks using a sliding window approach.
        Tries to break on paragraph boundaries for cleaner chunks.

        Args:
            text: Full document text.

        Returns:
            List of text chunks.
        """
        if not self.needs_chunking(text):
            return [text]

        # Convert token sizes to approximate character counts
        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4

        chunks = []
        # Split into paragraphs first for cleaner breaks
        paragraphs = text.split('\n\n')

        current_chunk = ""
        for paragraph in paragraphs:
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) > char_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Keep overlap from end of previous chunk
                overlap_text = current_chunk[-char_overlap:] if len(current_chunk) > char_overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def needs_map_reduce(self, chunks: List[str]) -> bool:
        """
        Check if map-reduce strategy should be applied.
        PRD: apply map-reduce for documents with more than 5 chunks.

        Args:
            chunks: List of text chunks.

        Returns:
            True if map-reduce is needed.
        """
        return len(chunks) > 5


class MapReduceProcessor:
    """
    Implements map-reduce summarization strategy for long documents.

    Strategy:
    1. MAP: Summarize each chunk independently
    2. REDUCE: Combine chunk summaries into a final comprehensive summary
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with Gemini API.

        Args:
            api_key: Gemini API key (or use GOOGLE_API_KEY env var).
        """
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    @retry_with_backoff(retries=5)
    def _generate_content(self, prompt: str):
        """Helper to call Gemini with retry logic."""
        return self.model.generate_content(prompt)

    def map_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """
        MAP phase: Summarize a single chunk.

        Args:
            chunk: Text chunk to summarize.
            chunk_index: Index of this chunk (0-based).
            total_chunks: Total number of chunks.

        Returns:
            Summary of the chunk.
        """
        prompt = f"""You are summarizing part {chunk_index + 1} of {total_chunks} of an educational document.
Extract the key information, concepts, and important details from this section.
Preserve any specific facts, definitions, formulas, or examples.

Text chunk:
{chunk}

Provide a comprehensive summary of this section that preserves all educational content.
Respond with only the summary text, no additional formatting."""

        try:
            response = self._generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error in map phase for chunk {chunk_index + 1}: {e}")
            # Fall back to truncating the chunk
            return chunk[:2000]

    def reduce_summaries(
        self,
        chunk_summaries: List[str],
        student_level: str = "undergraduate",
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict:
        """
        REDUCE phase: Combine chunk summaries into final educational outputs.

        Args:
            chunk_summaries: List of summaries from the MAP phase.
            student_level: Target student level.
            subject: Subject for context.
            topic: Topic for context.

        Returns:
            Complete study package dictionary.
        """
        combined_text = "\n\n---\n\n".join(
            f"[Section {i+1}]\n{summary}"
            for i, summary in enumerate(chunk_summaries)
        )

        context = ""
        if subject:
            context += f"Subject: {subject}\n"
        if topic:
            context += f"Topic: {topic}\n"

        prompt = f"""You are an expert educational content specialist. You have been given summaries of different sections of a long educational document. Generate comprehensive study materials from these combined summaries.

{context}
Student Level: {student_level}

Combined Section Summaries:
{combined_text}

Generate the FOLLOWING in JSON format:

1. LEVELED SUMMARY: A cohesive summary combining all sections, adapted to {student_level} comprehension level.
2. KEY CONCEPTS: List of 5+ core concepts with brief explanations drawn from across ALL sections.
3. FLASHCARDS: 6+ question-answer pairs for active recall, covering content from all sections, with difficulty tags.
4. EXAM QUESTIONS: 4+ questions covering Bloom's taxonomy (recall, understand, apply, analyze) with difficulty and model answers.

Respond ONLY with valid JSON:
{{
    "summary": {{
        "title": "Summary Title",
        "content": "Cohesive leveled summary text",
        "length_level": "brief|moderate|detailed"
    }},
    "concepts": [
        {{
            "name": "Concept Name",
            "definition": "Brief definition",
            "importance": "high|medium|low"
        }}
    ],
    "flashcards": [
        {{
            "question": "Question text",
            "answer": "Answer text",
            "difficulty": "easy|medium|hard",
            "tags": ["tag1", "tag2"]
        }}
    ],
    "questions": [
        {{
            "question": "Question text",
            "question_type": "recall|understand|apply|analyze",
            "difficulty": "easy|medium|hard",
            "model_answer": "Expected answer",
            "explanation": "Why this is correct"
        }}
    ]
}}"""

        try:
            response = self._generate_content(prompt)
            result = clean_json_response(response.text)
            return {
                "success": True,
                "data": result,
                "student_level": student_level,
                "processing_method": "map_reduce",
                "chunks_processed": len(chunk_summaries)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {},
                "processing_method": "map_reduce"
            }

    def process(
        self,
        chunks: List[str],
        student_level: str = "undergraduate",
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict:
        """
        Full map-reduce pipeline.

        Args:
            chunks: List of text chunks.
            student_level: Target student level.
            subject: Subject context.
            topic: Topic context.

        Returns:
            Complete study package.
        """
        # MAP phase: summarize each chunk
        print(f"  MAP phase: summarizing {len(chunks)} chunks...")
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = self.map_chunk(chunk, i, len(chunks))
            chunk_summaries.append(summary)
            print(f"    Chunk {i+1}/{len(chunks)} summarized")

        # REDUCE phase: combine into educational outputs
        print(f"  REDUCE phase: generating study package from {len(chunk_summaries)} summaries...")
        result = self.reduce_summaries(chunk_summaries, student_level, subject, topic)

        return result


def chunk_and_process(
    text: str,
    student_level: str = "undergraduate",
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Convenience function: chunk text if needed, apply map-reduce if necessary,
    or pass directly to EPF generator for short documents.

    Args:
        text: Full document text.
        student_level: Student level for adaptation.
        subject: Subject context.
        topic: Topic context.
        api_key: Optional Gemini API key.

    Returns:
        Study package result.
    """
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(text)

    if chunker.needs_map_reduce(chunks):
        # Long document: use map-reduce
        print(f"Document split into {len(chunks)} chunks — using map-reduce strategy")
        processor = MapReduceProcessor(api_key)
        return processor.process(chunks, student_level, subject, topic)
    else:
        # Short document or few chunks: concatenate and use direct EPF
        from app.llm.epf_generator import generate_study_package
        combined = "\n\n".join(chunks)
        print(f"Document has {len(chunks)} chunk(s) — using direct EPF generation")
        return generate_study_package(combined, student_level, subject, topic, api_key)
