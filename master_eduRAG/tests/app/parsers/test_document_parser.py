"""Tests for document type detection and parser selection."""

from pathlib import Path

import pytest

from app.parsers.document_parser import DocumentParserFactory, TXTParser, detect_file_type, parse_document


def test_detect_file_type_from_plain_text_extension(tmp_path: Path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello", encoding="utf-8")

    assert detect_file_type(str(file_path)) == "txt"


def test_parse_text_document_happy_path(tmp_path: Path):
    file_path = tmp_path / "lesson.txt"
    file_path.write_text("Photosynthesis stores energy.", encoding="utf-8")

    parsed = parse_document(str(file_path))

    assert parsed["text"] == "Photosynthesis stores energy."
    assert parsed["metadata"]["file_type"] == "txt"
    assert parsed["metadata"]["title"] == "lesson.txt"


def test_parser_factory_rejects_unknown_file_type(tmp_path: Path):
    file_path = tmp_path / "archive.bin"
    file_path.write_bytes(b"\x00\x01")

    with pytest.raises(ValueError, match="Unsupported file type"):
        DocumentParserFactory.get_parser(str(file_path))


def test_txt_parser_survives_invalid_utf8(tmp_path: Path):
    file_path = tmp_path / "bad.txt"
    file_path.write_bytes(b"valid\xfftext")

    assert TXTParser().extract_text(str(file_path)) == "validtext"
