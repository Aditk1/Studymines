"""
Database configuration and session management for EduSum.
Uses SQLAlchemy ORM with PostgreSQL backend.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file
load_dotenv()

# Database URL - Configure with your PostgreSQL credentials
# For local development, use SQLite; for production, use PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./edusum.db"  # SQLite for local development
)

# Create database engine
engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import models to register them with Base
    from app.models import User, Upload, Performance, Usage
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables (for testing/cleanup)."""
    Base.metadata.drop_all(bind=engine)
