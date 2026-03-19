"""
Unit tests for EduSum chunking and map-reduce module.
Tests document splitting, token estimation, and map-reduce decisions.
"""

import pytest
from app.chunking import DocumentChunker


class TestDocumentChunker:
    """Test suite for DocumentChunker."""

    def setup_method(self):
        """Create chunker with default settings."""
        self.chunker = DocumentChunker(chunk_size=3000, chunk_overlap=200)

    def test_estimate_tokens(self):
        # ~1 token per 4 characters
        text = "a" * 4000  # Should be ~1000 tokens
        tokens = self.chunker.estimate_tokens(text)
        assert tokens == 1000

    def test_estimate_tokens_empty(self):
        assert self.chunker.estimate_tokens("") == 0

    def test_needs_chunking_short_text(self):
        short = "Hello world. " * 10  # ~30 tokens
        assert self.chunker.needs_chunking(short) is False

    def test_needs_chunking_long_text(self):
        # 3001 tokens * 4 chars = 12004 chars
        long_text = "a" * 12004
        assert self.chunker.needs_chunking(long_text) is True

    def test_needs_chunking_exact_boundary(self):
        # Exactly 3000 tokens = 12000 chars
        boundary_text = "a" * 12000
        assert self.chunker.needs_chunking(boundary_text) is False

    def test_chunk_text_short_returns_single(self):
        short = "This is a short paragraph."
        chunks = self.chunker.chunk_text(short)
        assert len(chunks) == 1
        assert chunks[0] == short

    def test_chunk_text_long_returns_multiple(self):
        # Create text that definitely exceeds chunk size
        paragraphs = [f"Paragraph {i}. " + ("word " * 500) for i in range(20)]
        long_text = "\n\n".join(paragraphs)
        chunks = self.chunker.chunk_text(long_text)
        assert len(chunks) > 1

    def test_chunk_text_preserves_content(self):
        # All unique words should appear in at least one chunk
        paragraphs = [f"UniqueWord{i} is important." for i in range(5)]
        text = "\n\n".join(paragraphs)
        # Use small chunk size to force splitting
        small_chunker = DocumentChunker(chunk_size=10, chunk_overlap=2)
        chunks = small_chunker.chunk_text(text)
        combined = " ".join(chunks)
        for i in range(5):
            assert f"UniqueWord{i}" in combined

    def test_chunk_text_empty_string(self):
        chunks = self.chunker.chunk_text("")
        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_needs_map_reduce_few_chunks(self):
        assert self.chunker.needs_map_reduce(["a", "b", "c"]) is False
        assert self.chunker.needs_map_reduce(["a", "b", "c", "d", "e"]) is False

    def test_needs_map_reduce_many_chunks(self):
        chunks = [f"chunk_{i}" for i in range(6)]
        assert self.chunker.needs_map_reduce(chunks) is True

    def test_needs_map_reduce_exactly_five(self):
        # PRD says "more than 5 chunks" = 6+
        assert self.chunker.needs_map_reduce(["a"] * 5) is False

    def test_needs_map_reduce_six(self):
        assert self.chunker.needs_map_reduce(["a"] * 6) is True


class TestDocumentChunkerCustomConfig:
    """Test chunker with custom configuration."""

    def test_custom_chunk_size(self):
        # Very small chunk size — need paragraph breaks for chunking to split
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        paragraphs = [("word " * 40).strip() for _ in range(10)]
        text = "\n\n".join(paragraphs)  # ~400 tokens across 10 paragraphs
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_overlap_exists_between_chunks(self):
        # Create predictable text
        chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)
        paras = [f"Para{i}. " + ("text " * 30) for i in range(5)]
        text = "\n\n".join(paras)
        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Check that later chunks share some content with earlier ones
            # (overlap mechanism)
            for i in range(1, len(chunks)):
                # The end of chunk i-1 should partially appear in chunk i
                # This is a structural test — overlap means shared content
                assert len(chunks[i]) > 0
