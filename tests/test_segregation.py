"""
Unit tests for EduSum content segregation module.
Tests manual segregation, auto-segregation interface, and convenience function.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.segregation import ContentSegregator, segregate_content


class TestContentSegregator:
    """Test suite for ContentSegregator."""

    # --- Manual Segregation ---

    def test_manual_segregate(self):
        seg = ContentSegregator.__new__(ContentSegregator)
        result = seg.manual_segregate("Mathematics", "Algebra")
        assert result["subject"] == "Mathematics"
        assert result["topic"] == "Algebra"
        assert result["method"] == "manual"

    def test_manual_segregate_strips_whitespace(self):
        seg = ContentSegregator.__new__(ContentSegregator)
        result = seg.manual_segregate("  Biology  ", "  Photosynthesis  ")
        assert result["subject"] == "Biology"
        assert result["topic"] == "Photosynthesis"

    # --- Segregation Logic ---

    def test_segregate_prefers_manual_when_both_provided(self):
        seg = ContentSegregator.__new__(ContentSegregator)
        result = seg.segregate(
            text="Some content about math",
            manual_subject="Mathematics",
            manual_topic="Calculus"
        )
        assert result["subject"] == "Mathematics"
        assert result["topic"] == "Calculus"
        assert result["method"] == "manual"

    def test_segregate_falls_back_to_auto_when_no_manual(self):
        """When no manual input, auto_segregate should be called."""
        seg = ContentSegregator.__new__(ContentSegregator)
        # Mock the auto_segregate method
        seg.auto_segregate = MagicMock(return_value={
            "subject": "Physics",
            "topic": "Mechanics",
            "method": "auto",
            "confidence": "high"
        })
        
        result = seg.segregate(text="Newton's laws of motion")
        seg.auto_segregate.assert_called_once()
        assert result["method"] == "auto"

    def test_segregate_needs_both_manual_fields(self):
        """If only subject is provided (no topic), should fall back to auto."""
        seg = ContentSegregator.__new__(ContentSegregator)
        seg.auto_segregate = MagicMock(return_value={
            "subject": "Auto", "topic": "Auto", "method": "auto"
        })
        
        result = seg.segregate(
            text="Some text",
            manual_subject="Mathematics",
            manual_topic=None  # Topic missing
        )
        seg.auto_segregate.assert_called_once()


class TestSegregateContentFunction:
    """Test the convenience function."""

    def test_manual_segregation_via_function(self):
        result = segregate_content(
            text="Doesn't matter for manual",
            manual_subject="History",
            manual_topic="World War 2"
        )
        assert result["subject"] == "History"
        assert result["topic"] == "World War 2"
        assert result["method"] == "manual"
