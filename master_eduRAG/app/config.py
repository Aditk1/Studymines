"""
Unified configuration for master_eduRAG.
Merges Studymines app config with RLM-GraphRAG pipeline config.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./master_edurag.db")

# ── Gemini (Studymines Vision + EPF) ──────────────────────────
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")
DEFAULT_MODEL = "gemini-3-flash-preview"
VISION_MODEL = "gemini-3-flash-preview"

# ── RLM-GraphRAG LLM ─────────────────────────────────────────
RAG_LLM_PROVIDER = os.getenv("RAG_LLM_PROVIDER", "ollama")

# ── Application ───────────────────────────────────────────────
APP_NAME = "master_eduRAG"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ── Upload Limits ─────────────────────────────────────────────
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 10 * 1024 * 1024))
ALLOWED_DOCUMENT_TYPES = ["pdf", "pptx", "docx", "txt"]
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp", "heic"]

# ── Processing ────────────────────────────────────────────────
MAX_TOKENS = 3000
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 200
PROCESSING_TIMEOUT = 15

# ── Student Levels ────────────────────────────────────────────
STUDENT_LEVELS = ["high_school", "undergraduate", "postgraduate"]
DEFAULT_STUDENT_LEVEL = "undergraduate"

# ── EPF Output minimums ───────────────────────────────────────
MIN_CONCEPTS = 5
MIN_FLASHCARDS = 6
MIN_QUESTIONS = 4

# ── CORS ──────────────────────────────────────────────────────
CORS_ORIGINS = ["*"]
DB_ECHO = DEBUG
