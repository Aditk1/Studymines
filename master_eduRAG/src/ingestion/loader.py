"""
Document loading and chunking.
Supports plain text, Markdown, and PDF inputs.

PDF extraction priority:
  1. PyMuPDF (fitz)   — best for LaTeX/ArXiv papers, two-column layouts
  2. pdfplumber       — fallback for scanned or form-based PDFs
  3. Empty string     — if both fail, logs warning
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("loader")


@dataclass
class DocumentChunk:
    """A single chunk of text from a document."""
    text: str
    source: str
    chunk_idx: int
    metadata: dict = field(default_factory=dict)


class DocumentLoader:
    """Load documents from file paths or raw strings."""

    @staticmethod
    def load_file(path: str | Path) -> str:
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return DocumentLoader._load_pdf(path)
        else:
            return path.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _load_pdf(path: Path) -> str:
        """
        Try PyMuPDF first (best for ArXiv/LaTeX papers),
        fall back to pdfplumber, then warn if both fail.
        """
        # ── Attempt 1: PyMuPDF ──────────────────────────────────────
        try:
            import fitz  # type: ignore  (pymupdf)
            doc = fitz.open(str(path))
            pages = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    pages.append(text)
            doc.close()
            full_text = "\n\n".join(pages)
            if len(full_text.strip()) > 200:
                logger.info(
                    "pdf_loaded_pymupdf",
                    path=str(path),
                    chars=len(full_text),
                    pages=len(pages),
                )
                return full_text
            else:
                logger.warning(
                    "pymupdf_low_output",
                    chars=len(full_text),
                    msg="Trying pdfplumber fallback",
                )
        except ImportError:
            logger.warning(
                "pymupdf_not_installed",
                msg="pip install pymupdf  ← recommended for ArXiv papers",
            )
        except Exception as e:
            logger.warning("pymupdf_failed", error=str(e))

        # ── Attempt 2: pdfplumber ────────────────────────────────────
        try:
            import pdfplumber  # type: ignore
            with pdfplumber.open(path) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            full_text = "\n\n".join(p for p in pages if p.strip())
            if len(full_text.strip()) > 200:
                logger.info(
                    "pdf_loaded_pdfplumber",
                    path=str(path),
                    chars=len(full_text),
                )
                return full_text
            else:
                logger.warning("pdfplumber_low_output", chars=len(full_text))
        except ImportError:
            logger.warning("pdfplumber_not_installed", msg="pip install pdfplumber")
        except Exception as e:
            logger.warning("pdfplumber_failed", error=str(e))

        # ── Failure ──────────────────────────────────────────────────
        logger.error(
            "pdf_extraction_failed",
            path=str(path),
            msg="Both PyMuPDF and pdfplumber failed or returned empty text. "
                "Install pymupdf: pip install pymupdf",
        )
        return ""

    @staticmethod
    def load_texts(texts: list[str], source_prefix: str = "doc") -> list[tuple[str, str]]:
        """Return list of (text, source_name) pairs."""
        return [(t, f"{source_prefix}_{i}") for i, t in enumerate(texts)]


class Chunker:
    """
    Splits documents into overlapping text chunks.
    Uses sentence-aware splitting to avoid cutting mid-sentence.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, source: str = "") -> list[DocumentChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Raw document text.
            source: Source identifier for the document.

        Returns:
            List of DocumentChunk objects.
        """
        # Clean up common PDF extraction artifacts
        text = self._clean_pdf_text(text)

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            logger.warning("no_sentences_found", source=source, text_len=len(text))
            return []

        chunks: list[DocumentChunk] = []
        current_sentences: list[str] = []
        current_word_count = 0
        chunk_idx = 0

        for sentence in sentences:
            words = sentence.split()
            word_count = len(words)

            if current_word_count + word_count > self.chunk_size and current_sentences:
                # Emit current chunk
                chunk_text = " ".join(current_sentences)
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    source=source,
                    chunk_idx=chunk_idx,
                ))
                chunk_idx += 1

                # Overlap: keep last N words worth of sentences
                overlap_sentences: list[str] = []
                overlap_words = 0
                for sent in reversed(current_sentences):
                    sent_wc = len(sent.split())
                    if overlap_words + sent_wc <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_words += sent_wc
                    else:
                        break
                current_sentences = overlap_sentences
                current_word_count = overlap_words

            current_sentences.append(sentence)
            current_word_count += word_count

        # Final chunk
        if current_sentences:
            chunks.append(DocumentChunk(
                text=" ".join(current_sentences),
                source=source,
                chunk_idx=chunk_idx,
            ))

        logger.info(
            "document_chunked",
            source=source,
            num_chunks=len(chunks),
            total_sentences=len(sentences),
        )
        return chunks

    @staticmethod
    def _clean_pdf_text(text: str) -> str:
        """
        Clean common PDF extraction artifacts:
        - Remove hyphenation at line breaks (re-join words)
        - Collapse multiple newlines
        - Remove page numbers and headers that sneak in
        - Fix ligature characters
        """
        # Rejoin hyphenated line breaks: "trans-\nformer" → "transformer"
        text = re.sub(r"-\n(\w)", r"\1", text)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Fix common ligatures from PDF encoding
        text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff")
        text = text.replace("ﬃ", "ffi").replace("ﬄ", "ffl")
        # Remove standalone page numbers
        text = re.sub(r"\n\s*\d{1,3}\s*\n", "\n", text)
        return text

    def chunk_documents(
        self,
        docs: list[tuple[str, str]],
    ) -> list[DocumentChunk]:
        """Chunk a list of (text, source) pairs."""
        all_chunks: list[DocumentChunk] = []
        for text, source in docs:
            if not text.strip():
                logger.warning("empty_document", source=source)
                continue
            all_chunks.extend(self.chunk_text(text, source))
        return all_chunks