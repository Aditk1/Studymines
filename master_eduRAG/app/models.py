"""
Unified database models for master_eduRAG.
Includes Studymines user/upload models AND new GraphEntity model
for tracking Knowledge Graph data alongside relational data.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, Text, Interval, Boolean, JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """Student / user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    student_level = Column(String(50), nullable=False, default="undergraduate")
    created_at = Column(DateTime, default=datetime.utcnow)

    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")
    performance = relationship("Performance", back_populates="user", cascade="all, delete-orphan")
    usage = relationship("Usage", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Upload(Base):
    """Document / image upload record."""
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    subject = Column(String(100), nullable=True)
    topic = Column(String(100), nullable=True)
    file_path = Column(String(512), nullable=True)
    study_package = Column(Text, nullable=True)
    # ── NEW: Graph integration fields ──
    graph_path = Column(String(512), nullable=True)
    graph_triples_count = Column(Integer, nullable=True)
    graph_confidence = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploads")
    performance = relationship("Performance", back_populates="upload", cascade="all, delete-orphan")
    entities = relationship("GraphEntity", back_populates="upload", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Upload {self.file_name}>"


class Performance(Base):
    """Quiz scores and feedback."""
    __tablename__ = "performance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    score = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="performance")
    upload = relationship("Upload", back_populates="performance")

    def __repr__(self):
        return f"<Performance user={self.user_id} score={self.score}>"


class Usage(Base):
    """Session tracking and API call counts."""
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_duration = Column(Interval, nullable=True)
    api_calls = Column(Integer, default=0)
    logged_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="usage")

    def __repr__(self):
        return f"<Usage user={self.user_id} calls={self.api_calls}>"


class GraphEntity(Base):
    """
    NEW: Tracks Knowledge Graph entities extracted via RLM-GraphRAG.
    Links graph nodes back to the Upload that produced them,
    enabling cascade deletion and mastery tracking.
    """
    __tablename__ = "graph_entities"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    entity_name = Column(String(512), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)
    community_id = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    mastery_score = Column(Float, default=0.0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    upload = relationship("Upload", back_populates="entities")

    def __repr__(self):
        return f"<GraphEntity {self.entity_name}>"
