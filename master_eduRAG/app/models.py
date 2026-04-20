"""
Unified database models for master_eduRAG.
Includes Studymines user/upload models AND new GraphEntity model
for tracking Knowledge Graph data alongside relational data.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, Text, Interval, Boolean, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class User(Base):
    """Mapped to exact Supabase StudyPoint users table."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)

    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column("full_name", String(255), nullable=True)
    password_hash = Column(Text, nullable=True)
    student_level = Column(String(50), default="undergraduate")

    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    job_title = Column(String(100), nullable=True)

    role = Column(String(50), default="student")
    status = Column(String(50), default="active")
    is_active = Column(Boolean, default=True)

    preferences = Column(JSONB, default=lambda: {"theme": "system", "notifications": True})
    
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")
    performance = relationship("Performance", back_populates="user", cascade="all, delete-orphan")
    usage = relationship("Usage", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("LMSReminder", back_populates="user", cascade="all, delete-orphan")
    
    # ── LMS Relationships ──
    courses_taught = relationship("Course", back_populates="instructor", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    assessment_attempts = relationship("AssessmentAttempt", back_populates="user", cascade="all, delete-orphan")
    risk_flags = relationship("AcademicRisk", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Upload(Base):
    """Document / image upload record."""
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
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
    __tablename__ = "edurag_performance"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
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
    __tablename__ = "edurag_usage"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_duration = Column(Interval, nullable=True)
    api_calls = Column(Integer, default=0)
    logged_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="usage")

    def __repr__(self):
        return f"<Usage user={self.user_id} calls={self.api_calls}>"



class GraphEntity(Base):
    """
    Tracks Knowledge Graph entities extracted via RLM-GraphRAG.
    Links graph nodes back to the Upload that produced them.
    """
    __tablename__ = "graph_entities"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    entity_name = Column(String(512), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)
    community_id = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    mastery_score = Column(Float, default=0.0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    upload = relationship("Upload", back_populates="entities")
    question_bank = relationship("QuestionBank", back_populates="entity")


# ═══════════════════════════════════════════════════════════════
# LMS CORE MODELS
# ═══════════════════════════════════════════════════════════════

class Course(Base):
    """Top-level container for educational content."""
    __tablename__ = "lms_courses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True)
    status = Column(String(50), default="draft")  # draft, published, archived
    created_at = Column(DateTime, default=datetime.utcnow)

    instructor = relationship("User", back_populates="courses_taught")
    sections = relationship("Section", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course {self.title}>"


class Assessment(Base):
    """LMS Assessment / Exam."""
    __tablename__ = "lms_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    course_id = Column(Integer, ForeignKey("lms_courses.id"), nullable=True)
    classroom_id = Column(String(36), ForeignKey("lms_classrooms.id"), nullable=True)
    module_id = Column(Integer, ForeignKey("lms_modules.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_points = Column(Integer, default=100)
    time_limit = Column(Integer, nullable=True)  # in minutes
    passing_score = Column(Float, default=60.0)
    
    is_published = Column(Boolean, default=False)
    randomize_questions = Column(Boolean, default=True)
    question_ids = Column(JSON, nullable=True)   # Array of QuestionBank IDs
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="assessments")
    classroom = relationship("Classroom", back_populates="assessments")
    module = relationship("LessonModule", back_populates="assessment")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class Section(Base):
    """Logical grouping of modules within a course."""
    __tablename__ = "lms_sections"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    course_id = Column(Integer, ForeignKey("lms_courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    order = Column(Integer, default=0)
    summary = Column(Text, nullable=True)

    course = relationship("Course", back_populates="sections")
    modules = relationship("LessonModule", back_populates="section", cascade="all, delete-orphan")


class LessonModule(Base):
    """Individual learning unit (Video, Document, Quiz)."""
    __tablename__ = "lms_modules"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    section_id = Column(Integer, ForeignKey("lms_sections.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)  # video, document, quiz, assignment
    content_data = Column(JSON, nullable=True)       # Store links, text, or metadata
    order = Column(Integer, default=0)
    
    # Adaptive logic
    is_conditional = Column(Boolean, default=False)
    unlock_condition = Column(JSON, nullable=True)    # {"min_mastery": 0.7, "entity_id": 101}

    section = relationship("Section", back_populates="modules")
    assessment = relationship("Assessment", back_populates="module", uselist=False, cascade="all, delete-orphan")


class Enrollment(Base):
    """Student enrollment record with progress tracking."""
    __tablename__ = "lms_enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("lms_courses.id"), nullable=False)
    progress_percent = Column(Float, default=0.0)
    status = Column(String(50), default="active")  # active, completed, dropped, at_risk
    enrolled_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


# ═══════════════════════════════════════════════════════════════
# ASSESSMENT & MASTERY
# ═══════════════════════════════════════════════════════════════

class QuestionBank(Base):
    """Reusable questions linked to Knowledge Graph entities."""
    __tablename__ = "lms_question_bank"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    subject = Column(String(100), nullable=True)
    topic = Column(String(100), nullable=True)
    entity_id = Column(Integer, ForeignKey("graph_entities.id"), nullable=True)
    
    question_type = Column(String(50), default="multiple_choice")  # mcq, msq, open, boolean
    difficulty = Column(Integer, default=1)  # 1-5
    content = Column(JSON, nullable=False)   # {"question": "...", "options": [...], "answer": "..."}
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entity = relationship("GraphEntity", back_populates="question_bank")




class AssessmentAttempt(Base):
    """Student performance on an assessment."""
    __tablename__ = "lms_assessment_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("lms_assessments.id"), nullable=False)
    score = Column(Float, nullable=False)
    is_passed = Column(Boolean, default=False)
    responses = Column(JSON, nullable=True)      # Student's actual answers
    ai_feedback = Column(Text, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="assessment_attempts")
    assessment = relationship("Assessment", back_populates="attempts")


class AcademicRisk(Base):
    """Tracks students at risk using GraphRAG mastery + engagement data."""
    __tablename__ = "lms_academic_risk"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("lms_courses.id"), nullable=False)
    
    risk_score = Column(Float, default=0.0)      # 0-100
    risk_level = Column(String(50), default="low") # low, medium, high, critical
    flags = Column(JSON, nullable=True)          # ["low_engagement", "poor_concept_mastery"]
    
    analysis_data = Column(JSON, nullable=True)  # Detail for the AI Risk report
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="risk_flags")


class EventLog(Base):
    """Raw analytics events for student behavior tracking."""
    __tablename__ = "lms_event_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False, index=True) # click, view, query, finish_video
    path = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)   # session_id, time_spent, element_id
    timestamp = Column(DateTime, default=datetime.utcnow)


class MasteryLog(Base):
    """Historical tracking of concept mastery over time (GraphRAG integration)."""
    __tablename__ = "lms_mastery_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("graph_entities.id"), nullable=False)
    score = Column(Float, nullable=False)
    source_type = Column(String(50), nullable=True) # assessment, query_context, manual_review
    logged_at = Column(DateTime, default=datetime.utcnow)
class LMSReminder(Base):
    """Personalized reminders or scheduled tasks for students/teachers."""
    __tablename__ = "lms_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reminder_type = Column(String(50), default="task")  # study, quiz, assignment, personal
    due_at = Column(DateTime, nullable=False)
    priority = Column(String(20), default="medium")    # low, medium, high
    status = Column(String(20), default="pending")      # pending, completed, dismissed
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reminders")
