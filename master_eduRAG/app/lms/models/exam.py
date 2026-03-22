import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Exam(Base):
    __tablename__ = "lms_exams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    exam_type = Column(String(50), nullable=False)
    
    time_limit_minutes = Column(Integer, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    from sqlalchemy.dialects.postgresql import UUID
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    classroom_links = relationship("ExamClassroom", back_populates="exam", cascade="all, delete-orphan")
    submissions = relationship("ExamSubmission", back_populates="exam", cascade="all, delete-orphan")

class ExamClassroom(Base):
    __tablename__ = "lms_exam_classrooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exam_id = Column(String(36), ForeignKey("lms_exams.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(String(36), ForeignKey("lms_classrooms.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("exam_id", "classroom_id", name="uq_lms_exam_classroom"),
    )

    exam = relationship("Exam", back_populates="classroom_links")

class ExamSubmission(Base):
    __tablename__ = "lms_exam_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exam_id = Column(String(36), ForeignKey("lms_exams.id", ondelete="CASCADE"), nullable=False, index=True)
    from sqlalchemy.dialects.postgresql import UUID
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    answers = Column(JSON, nullable=False)
    score = Column(Float, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_lms_exam_student"),
    )

    exam = relationship("Exam", back_populates="submissions")
