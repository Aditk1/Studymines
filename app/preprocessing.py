"""
Text preprocessing module for EduSum.
Handles cleaning, normalization, and structuring of extracted text.
"""

import re
from typing import Optional


class TextPreprocessor:
    """Preprocesses extracted text for quality and consistency."""

    def __init__(self):
        """Initialize preprocessor."""
        pass

    def clean_whitespace(self, text: str) -> str:
        """Remove extra whitespace and normalize line breaks."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline (paragraph breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text

    def fix_encoding(self, text: str) -> str:
        """Fix common encoding issues (UTF-8)."""
        try:
            # Encode to bytes and back to handle encoding issues
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            pass
        return text

    def normalize_bullets(self, text: str) -> str:
        """Normalize bullet points and list markers."""
        # Convert various bullet styles to standard dash
        text = re.sub(r'[•◦▪]', '-', text)
        text = re.sub(r'[→]', '->', text)
        return text

    def remove_page_artifacts(self, text: str) -> str:
        """Remove common page artifacts (headers, footers, page numbers)."""
        # Remove standalone page numbers
        text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
        # Remove common header/footer patterns
        text = re.sub(r'Page \d+', '', text)
        return text

    def normalize_quotes(self, text: str) -> str:
        """Normalize smart quotes to standard quotes."""
        # Use Unicode codepoints to avoid encoding issues across platforms
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # left/right double quotes
        text = text.replace('\u2018', "'").replace('\u2019', "'")  # left/right single quotes
        return text

    def preserve_structure(self, text: str) -> str:
        """Preserve document structure (headings, lists)."""
        # Ensure consistent spacing around common section markers
        text = re.sub(r'\n(#{1,6}\s)', r'\n\n\1', text)  # Markdown-style headings
        text = re.sub(r'(\n-\s)', r'\n\1', text)  # List items
        return text

    def preprocess(self, raw_text: str) -> str:
        """
        Apply all preprocessing steps in sequence.
        
        Args:
            raw_text: Raw extracted text.
            
        Returns:
            Cleaned and normalized text.
        """
        # Apply fixes in order
        text = self.fix_encoding(raw_text)
        text = self.normalize_quotes(text)
        text = self.normalize_bullets(text)
        text = self.remove_page_artifacts(text)
        text = self.preserve_structure(text)
        text = self.clean_whitespace(text)
        
        return text


def preprocess_text(text: str) -> str:
    """
    Convenience function for preprocessing text.
    
    Args:
        text: Raw text to preprocess.
        
    Returns:
        Cleaned text.
    """
    processor = TextPreprocessor()
    return processor.preprocess(text)
