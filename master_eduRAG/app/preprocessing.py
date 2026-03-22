"""
Text preprocessing module.
Handles cleaning, normalization, and structuring of extracted text.
"""

import re
from typing import Optional


class TextPreprocessor:
    """Preprocesses extracted text for quality and consistency."""

    def clean_whitespace(self, text: str) -> str:
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def fix_encoding(self, text: str) -> str:
        try:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception:
            pass
        return text

    def normalize_bullets(self, text: str) -> str:
        text = re.sub(r'[•◦▪]', '-', text)
        text = re.sub(r'[→]', '->', text)
        return text

    def remove_page_artifacts(self, text: str) -> str:
        text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Page \d+', '', text)
        return text

    def normalize_quotes(self, text: str) -> str:
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        return text

    def preserve_structure(self, text: str) -> str:
        text = re.sub(r'\n(#{1,6}\s)', r'\n\n\1', text)
        text = re.sub(r'(\n-\s)', r'\n\1', text)
        return text

    def preprocess(self, raw_text: str) -> str:
        text = self.fix_encoding(raw_text)
        text = self.normalize_quotes(text)
        text = self.normalize_bullets(text)
        text = self.remove_page_artifacts(text)
        text = self.preserve_structure(text)
        text = self.clean_whitespace(text)
        return text


def preprocess_text(text: str) -> str:
    """Convenience function."""
    return TextPreprocessor().preprocess(text)
