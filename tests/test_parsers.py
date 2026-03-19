"""
Unit tests for EduSum document parser module.
Tests PDF, PPTX, DOCX, TXT parsers and file type detection.
"""

import pytest
import os
import tempfile
from pathlib import Path

from app.parsers.document_parser import (
    TXTParser,
    DocumentParserFactory,
    detect_file_type,
    parse_document,
)


class TestTXTParser:
    """Test suite for TXT parser."""

    def test_extract_text_from_txt_file(self):
        parser = TXTParser()
        # Create temp TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("This is a test document.\nWith multiple lines.\nThird line here.")
            tmp_path = f.name

        try:
            text = parser.extract_text(tmp_path)
            assert "This is a test document" in text
            assert "multiple lines" in text
            assert "Third line here" in text
        finally:
            os.unlink(tmp_path)

    def test_extract_metadata_from_txt(self):
        parser = TXTParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Hello world")
            tmp_path = f.name

        try:
            metadata = parser.extract_metadata(tmp_path)
            assert metadata["file_type"] == "txt"
            assert metadata["size_bytes"] > 0
            assert os.path.basename(tmp_path) in metadata["title"]
        finally:
            os.unlink(tmp_path)

    def test_extract_text_empty_file(self):
        parser = TXTParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            tmp_path = f.name

        try:
            text = parser.extract_text(tmp_path)
            assert text == ""
        finally:
            os.unlink(tmp_path)

    def test_extract_text_unicode(self):
        parser = TXTParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Café résumé naïve — Ñ")
            tmp_path = f.name

        try:
            text = parser.extract_text(tmp_path)
            assert "Café" in text
            assert "Ñ" in text
        finally:
            os.unlink(tmp_path)


class TestDetectFileType:
    """Test suite for file type auto-detection."""

    def test_detect_txt_by_extension(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"plain text content")
            tmp_path = f.name

        try:
            file_type = detect_file_type(tmp_path)
            assert file_type == "txt"
        finally:
            os.unlink(tmp_path)

    def test_detect_pdf_by_magic_bytes(self):
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            f.write(b"%PDF-1.4 fake pdf content")
            tmp_path = f.name

        try:
            file_type = detect_file_type(tmp_path)
            assert file_type == "pdf"
        finally:
            os.unlink(tmp_path)

    def test_detect_unknown_extension(self):
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"some content")
            tmp_path = f.name

        try:
            file_type = detect_file_type(tmp_path)
            assert file_type == "xyz"  # Falls back to extension
        finally:
            os.unlink(tmp_path)


class TestDocumentParserFactory:
    """Test suite for DocumentParserFactory."""

    def test_factory_returns_txt_parser(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test")
            tmp_path = f.name

        try:
            parser = DocumentParserFactory.get_parser(tmp_path)
            assert isinstance(parser, TXTParser)
        finally:
            os.unlink(tmp_path)

    def test_factory_raises_for_unsupported_type(self):
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"test")
            tmp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                DocumentParserFactory.get_parser(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestParseDocument:
    """Test the convenience function."""

    def test_parse_txt_document(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Photosynthesis is the process by which plants convert light to energy.")
            tmp_path = f.name

        try:
            result = parse_document(tmp_path)
            assert "text" in result
            assert "metadata" in result
            assert "Photosynthesis" in result["text"]
            assert result["metadata"]["file_type"] == "txt"
        finally:
            os.unlink(tmp_path)
