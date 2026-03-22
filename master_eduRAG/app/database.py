"""
Database configuration and session management.
Uses SQLAlchemy ORM — SQLite for dev, PostgreSQL for production.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./master_edurag.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from app.models import User, Upload, Performance, Usage, GraphEntity
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables (testing only)."""
    Base.metadata.drop_all(bind=engine)
