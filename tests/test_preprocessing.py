"""
Unit tests for EduSum text preprocessing module.
Tests all preprocessing steps: encoding, whitespace, bullets, quotes, structure.
"""

import pytest
from app.preprocessing import TextPreprocessor, preprocess_text


class TestTextPreprocessor:
    """Test suite for TextPreprocessor class."""

    def setup_method(self):
        """Create preprocessor instance for each test."""
        self.preprocessor = TextPreprocessor()

    # --- clean_whitespace ---

    def test_clean_whitespace_removes_extra_spaces(self):
        text = "Hello    world   test"
        result = self.preprocessor.clean_whitespace(text)
        assert result == "Hello world test"

    def test_clean_whitespace_normalizes_newlines(self):
        text = "Para 1\n\n\n\n\nPara 2"
        result = self.preprocessor.clean_whitespace(text)
        assert result == "Para 1\n\nPara 2"

    def test_clean_whitespace_strips_edges(self):
        text = "   Hello world   "
        result = self.preprocessor.clean_whitespace(text)
        assert result == "Hello world"

    def test_clean_whitespace_empty_string(self):
        result = self.preprocessor.clean_whitespace("")
        assert result == ""

    # --- fix_encoding ---

    def test_fix_encoding_valid_utf8(self):
        text = "Hello world"
        result = self.preprocessor.fix_encoding(text)
        assert result == "Hello world"

    def test_fix_encoding_preserves_unicode(self):
        text = "Café résumé naïve"
        result = self.preprocessor.fix_encoding(text)
        assert "Café" in result

    # --- normalize_bullets ---

    def test_normalize_bullets_converts_bullet_chars(self):
        text = "• Item 1\n◦ Item 2\n▪ Item 3"
        result = self.preprocessor.normalize_bullets(text)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result

    def test_normalize_bullets_converts_arrows(self):
        text = "→ Next step"
        result = self.preprocessor.normalize_bullets(text)
        assert "-> Next step" in result

    def test_normalize_bullets_preserves_dashes(self):
        text = "- Already a dash"
        result = self.preprocessor.normalize_bullets(text)
        assert result == "- Already a dash"

    # --- remove_page_artifacts ---

    def test_remove_page_artifacts_removes_page_numbers(self):
        text = "Some content\n42\nMore content"
        result = self.preprocessor.remove_page_artifacts(text)
        assert "\n42\n" not in result

    def test_remove_page_artifacts_removes_page_x(self):
        text = "Content here Page 5 more content"
        result = self.preprocessor.remove_page_artifacts(text)
        assert "Page 5" not in result

    def test_remove_page_artifacts_preserves_normal_numbers(self):
        text = "There are 42 students in class"
        result = self.preprocessor.remove_page_artifacts(text)
        assert "42 students" in result

    # --- normalize_quotes ---

    def test_normalize_quotes_smart_double(self):
        text = '\u201cHello\u201d'  # "Hello"
        result = self.preprocessor.normalize_quotes(text)
        assert result == '"Hello"'

    def test_normalize_quotes_smart_single(self):
        text = '\u2018don\u2019t'  # 'don't
        result = self.preprocessor.normalize_quotes(text)
        assert result == "'don't"

    # --- preprocess (full pipeline) ---

    def test_preprocess_full_pipeline(self):
        raw = "   • Item 1\n\n\n\n\n◦ Item 2   \n\n\u201cHello\u201d   "
        result = self.preprocessor.preprocess(raw)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert '"Hello"' in result
        # Should not have excessive whitespace
        assert "\n\n\n" not in result

    def test_preprocess_empty_input(self):
        result = self.preprocessor.preprocess("")
        assert result == ""

    def test_preprocess_plain_text_unchanged(self):
        text = "This is a normal sentence with no issues."
        result = self.preprocessor.preprocess(text)
        assert result == text


# --- Convenience function ---

class TestPreprocessText:
    """Test the convenience function."""

    def test_preprocess_text_function(self):
        raw = "  Hello    world  "
        result = preprocess_text(raw)
        assert result == "Hello world"

    def test_preprocess_text_with_bullets(self):
        raw = "• First\n• Second"
        result = preprocess_text(raw)
        assert "- First" in result
        assert "- Second" in result
