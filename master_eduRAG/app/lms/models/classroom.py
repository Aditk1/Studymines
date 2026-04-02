import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models import Assessment

class Classroom(Base):
    __tablename__ = "lms_classrooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    
    subject = Column(String(100), nullable=True)
    grade_level = Column(String(50), nullable=True)
    cover_image_url = Column(Text, nullable=True)
    icon = Column(String(10), nullable=True)
    
    is_archived = Column(Boolean, default=False)
    settings = Column(JSON, default=dict)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    members = relationship("ClassroomMember", back_populates="classroom", cascade="all, delete-orphan")
    materials = relationship("LMSMaterial", back_populates="classroom", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="classroom", cascade="all, delete-orphan")

class ClassroomMember(Base):
    __tablename__ = "lms_classroom_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String(36), ForeignKey("lms_classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(String(50), default="student")
    status = Column(String(50), default="active")
    joined_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("classroom_id", "user_id", name="uq_lms_classroom_member"),
    )

    classroom = relationship("Classroom", back_populates="members")
