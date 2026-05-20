"""Tests for extracted-text normalization."""

from app.preprocessing import TextPreprocessor, preprocess_text


def test_preprocess_text_happy_path():
    raw = "  Title\n\n\n• Item 1\n→ next\nPage 2\n“quoted”  text  "

    cleaned = preprocess_text(raw)

    assert "- Item 1" in cleaned
    assert "-> next" in cleaned
    assert '"quoted" text' in cleaned
    assert "Page 2" not in cleaned


def test_preprocess_text_empty_input():
    assert preprocess_text("") == ""


def test_clean_whitespace_collapses_repeated_spaces_and_newlines():
    processor = TextPreprocessor()

    assert processor.clean_whitespace("a   b\n\n\n\nc") == "a b\n\nc"
