"""
Database models for EduSum using SQLAlchemy.
Includes users, uploads, performance, usage, and leaderboard data.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Interval
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model for storing student information."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Added for simple auth
    student_level = Column(String(50), nullable=False)  # high_school, undergraduate, postgraduate
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")
    performance = relationship("Performance", back_populates="user", cascade="all, delete-orphan")
    usage = relationship("Usage", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Upload(Base):
    """Upload model for storing document/image metadata."""
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, pptx, docx, image
    subject = Column(String(100), nullable=True)  # e.g., Mathematics, Biology
    topic = Column(String(100), nullable=True)  # e.g., Algebra, Photosynthesis
    study_package = Column(Text, nullable=True)  # JSON string of the generated study package
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="uploads")
    performance = relationship("Performance", back_populates="upload", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Upload {self.file_name}>"


class Performance(Base):
    """Performance model for storing quiz scores and feedback."""
    __tablename__ = "performance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0.0 - 5.0 (educational utility rating)
    notes = Column(Text, nullable=True)  # Additional feedback/notes
    completed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="performance")
    upload = relationship("Upload", back_populates="performance")

    def __repr__(self):
        return f"<Performance user={self.user_id} score={self.score}>"


class Usage(Base):
    """Usage model for tracking session time and API calls."""
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_duration = Column(Interval, nullable=True)  # Time spent in session
    api_calls = Column(Integer, default=0)  # Number of API calls made
    logged_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="usage")

    def __repr__(self):
        return f"<Usage user={self.user_id} calls={self.api_calls}>"
