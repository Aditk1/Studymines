import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class LMSMaterial(Base):
    __tablename__ = "lms_materials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    classroom_id = Column(String(36), ForeignKey("lms_classrooms.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    
    file_url = Column(Text, nullable=False)
    file_type = Column(String(20), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    ai_summary = Column(Text, nullable=True)
    ai_tags = Column(JSON, nullable=True)  # Using JSON instead of ARRAY
    
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # ── AI & Study Package Integration ──
    study_package = Column(Text, nullable=True)
    graph_path = Column(String(512), nullable=True)
    graph_triples_count = Column(Integer, nullable=True)
    graph_confidence = Column(Float, nullable=True)
    file_path = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, default=None)

    classroom = relationship("Classroom", back_populates="materials")
    chunks = relationship("DocumentChunk", back_populates="material", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "lms_document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String(36), ForeignKey("lms_materials.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    chunk_content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)

    material = relationship("LMSMaterial", back_populates="chunks")
