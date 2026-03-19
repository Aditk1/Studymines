"""
Configuration settings for EduSum.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/edusum_db"
)

# API Keys
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "")
DEFAULT_MODEL = "gemini-flash-latest"  
VISION_MODEL = "gemini-flash-latest" 

# Application
APP_NAME = "EduSum"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Upload limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_DOCUMENT_TYPES = ["pdf", "pptx", "docx", "txt"]
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp", "heic"]

# Processing
MAX_TOKENS = 3000
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 200
PROCESSING_TIMEOUT = 15  # seconds

# Student levels
STUDENT_LEVELS = ["high_school", "undergraduate", "postgraduate"]
DEFAULT_STUDENT_LEVEL = "undergraduate"

# Output requirements
MIN_CONCEPTS = 5
MIN_FLASHCARDS = 6
MIN_QUESTIONS = 4

# CORS
CORS_ORIGINS = ["*"]

# Database
DB_ECHO = DEBUG
