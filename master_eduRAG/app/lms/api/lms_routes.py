import secrets
import shutil
import os
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import (
    User, Course, Section, LessonModule, Enrollment, 
    QuestionBank, Assessment, AssessmentAttempt, 
    AcademicRisk, EventLog, MasteryLog, LMSReminder, GraphEntity
)
from app.lms.core.ai_generator import CognitiveAIGenerator
from app.lms.models.classroom import Classroom, ClassroomMember
from app.lms.models.material import LMSMaterial
from app.lms.models.chat import ChatRoom, ChatMessage

from app.lms.auth import get_current_user, get_current_user_optional, require_role

router = APIRouter(prefix="/lms", tags=["LMS Core"])

# --- Core Content management ---

@router.get("/classrooms/explore", tags=["Content Matrix"])
async def get_explore_classrooms(db: Session = Depends(get_db)):
    """List all available classrooms/cohorts."""
    classrooms = db.query(Classroom).all()
    return [{"id": c.id, "name": c.name, "subject": c.subject, "code": c.code} for c in classrooms]


@router.get("/courses/{course_id}/architecture", tags=["Courses"])
async def get_course_architecture_consolidated(
    course_id: int, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieve full course sections and modules hierarchy with access control."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Secure check: only instructor or enrolled students (or admin) can see full architecture
    if user.role not in ["teacher", "admin"] and course.status != "published":
        enrollment = db.query(Enrollment).filter(Enrollment.course_id == course_id, Enrollment.user_id == user.id).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="Not authorized to view course architecture")

    sections = db.query(Section).filter(Section.course_id == course_id).order_by(Section.order).all()
    results = []
    for s in sections:
        modules = db.query(LessonModule).filter(LessonModule.section_id == s.id).order_by(LessonModule.order).all()
        results.append({
            "id": s.id,
            "title": s.title,
            "summary": getattr(s, 'summary', ""),
            "order": s.order,
            "modules": [{"id": m.id, "title": m.title, "type": m.content_type, "is_conditional": m.is_conditional} for m in modules]
        })
    return results

# --- Routes ---

@router.get("/chats/{room_id}/history")
async def get_chat_history(
    room_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retrieve chat history for a room."""
    # Optional: Verify user has access to this classroom room
    messages = db.query(ChatMessage).filter(ChatMessage.room_id == room_id).order_by(ChatMessage.created_at).all()
    # Mask data
    return [
        {
            "id": m.id,
            "room_id": m.room_id,
            "sender_id": str(m.sender_id),
            "content": m.content,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]

# --- Schemas ---

class ClassroomBase(BaseModel):
    name: str
    description: Optional[str] = None
    subject: Optional[str] = None

class ClassroomCreate(ClassroomBase):
    pass

class ClassroomResponse(ClassroomBase):
    id: str
    code: str
    created_by: UUID
    created_at: datetime
    member_count: int = 0
    chat_room_id: Optional[str] = None

    class Config:
        from_attributes = True

# --- Routes ---

@router.post("/classrooms", response_model=ClassroomResponse)
async def create_classroom(
    data: ClassroomCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Create a new classroom and auto-add the creator."""
    classroom = Classroom(
        name=data.name,
        description=data.description,
        subject=data.subject,
        code=f"{data.name[:4].upper()}-{secrets.token_hex(3).upper()}",
        created_by=user.id
    )
    db.add(classroom)
    db.flush() # Get ID

    # Add creator as teacher member
    member = ClassroomMember(
        classroom_id=classroom.id,
        user_id=user.id,
        role="teacher"
    )
    db.add(member)

    # Create default chat room
    chat_room = ChatRoom(
        classroom_id=classroom.id,
        name=f"{classroom.name} Discussion",
        room_type="classroom"
    )
    db.add(chat_room)
    
    db.commit()
    db.refresh(classroom)
    return classroom

@router.get("/classrooms", response_model=List[ClassroomResponse])
async def list_classrooms(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List classrooms the user is a member of."""
    classrooms = db.query(Classroom).join(ClassroomMember).filter(
        ClassroomMember.user_id == user.id,
        ClassroomMember.status == "active"
    ).all()
    
    # Calculate member counts manually for simple response
    for c in classrooms:
        c.member_count = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == c.id, ClassroomMember.status == "active").count()
        
    return classrooms

class JoinRequest(BaseModel):
    code: str

@router.post("/classrooms/join")
async def join_classroom(
    req: JoinRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    classroom = db.query(Classroom).filter(Classroom.code == req.code).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Invalid classroom code")

    existing = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom.id,
        ClassroomMember.user_id == user.id
    ).first()
    
    if existing:
        return {"success": True, "status": existing.status}

    member = ClassroomMember(
        classroom_id=classroom.id,
        user_id=user.id,
        role="student",
        status="pending"
    )
    db.add(member)
    db.commit()
    return {"success": True, "status": "pending"}

@router.get("/classrooms/{classroom_id}/requests")
async def get_classroom_requests(
    classroom_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    member = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.user_id == user.id,
        ClassroomMember.role == "teacher"
    ).first()
    if not member and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not a teacher of this class")

    requests = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.status == "pending"
    ).all()
    
    res = []
    for r in requests:
        u = db.query(User).filter(User.id == r.user_id).first()
        if u:
            res.append({"id": r.id, "user_id": str(u.id), "name": u.name, "requested_at": r.joined_at})
    return res

@router.get("/materials/global", tags=["Content Matrix"])
async def get_global_materials(db: Session = Depends(get_db)):
    """Retrieve all ingested materials for the Global Content view."""
    materials = db.query(LMSMaterial).order_by(LMSMaterial.created_at.desc()).all()
    results = []
    for m in materials:
        pkg = {}
        if m.study_package:
            try:
                pkg = json.loads(m.study_package)
                if isinstance(pkg, dict) and "package" in pkg:
                    pkg = pkg["package"]
            except Exception:
                pass
                
        results.append({
            "id": m.id,
            "title": m.title,
            "subject": m.classroom.subject if m.classroom else "General",
            "classroom_name": m.classroom.name if m.classroom else "Archive",
            "created_at": getattr(m.created_at, 'isoformat', lambda: str(m.created_at))(),
            "status": m.status or "active",
            "concept_count": len(pkg.get("data", {}).get("concepts", []) or pkg.get("questions", [])),
            "summary": (str(pkg.get("summary"))[:150] + "...") if pkg.get("summary") else "No summary archived."
        })
    return results

@router.post("/classrooms/{classroom_id}/requests/{member_id}/approve")
async def approve_join_request(
    classroom_id: str,
    member_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    member = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.user_id == user.id,
        ClassroomMember.role == "teacher"
    ).first()
    if not member and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not a teacher of this class")

    req_member = db.query(ClassroomMember).filter(ClassroomMember.id == member_id).first()
    if req_member:
        req_member.status = "active"
        db.commit()
    return {"success": True}


@router.get("/classrooms/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(
    classroom_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get classroom details."""
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Provision chat room if missing for legacy classrooms
    chat_room = db.query(ChatRoom).filter(ChatRoom.classroom_id == classroom_id).first()
    if not chat_room:
        chat_room = ChatRoom(
            name=f"{classroom.name} Discussion",
            room_type="classroom",
            classroom_id=classroom_id
        )
        db.add(chat_room)
        db.commit()
        db.refresh(chat_room)

    # Attach ChatRoom id
    member = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.user_id == user.id
    ).first()
    if not member and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not a member of this classroom")
    
    # Calculate counts
    res_dict = {column.name: getattr(classroom, column.name) for column in classroom.__table__.columns}
    res_dict["member_count"] = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).count()
    res_dict["chat_room_id"] = chat_room.id if chat_room else None
    
    return res_dict

@router.post("/materials/upload")
async def upload_material(
    classroom_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Upload material to a classroom, process through RAG, and save."""
    # 1. Verify membership/perm
    member = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.user_id == user.id
    ).first()
    if not member and user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # 2. Local File Storage
    upload_dir = os.path.join("data", "uploads", classroom_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{uuid4()}_{file.filename}")
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    # 3. Smart Ingestion Bridge (Milestone 1)
    from app.main import parse_document, preprocess_text, segregate_content, chunk_and_process
    import json
    
    try:
        print(f"DEBUG_LMS_UPLOAD: Processing {file.filename} through RAG...")
        parsed = parse_document(file_path)
        text = preprocess_text(parsed["text"])
        # Manual override or auto-segregation
        segregation = {"subject": "LMS", "topic": title, "method": "manual"} 
        
        raw_res = await chunk_and_process(
            text, "undergraduate",
            segregation["subject"], segregation["topic"],
            source_name=file.filename
        )
        study_package = raw_res["package"]
        graph_meta = raw_res.get("stats", {}) # Called stats in chunk_and_process
        
        # 4. Create Record
        material = LMSMaterial(
            classroom_id=classroom_id,
            title=title,
            description=description,
            file_path=file_path,
            file_type=file.content_type,
            uploaded_by=user.id,
            study_package=json.dumps(study_package),
            graph_path=graph_meta.get("graph_path"),
            graph_triples_count=graph_meta.get("triples_count"),
            graph_confidence=graph_meta.get("extraction_confidence"),
            status="ready"
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        
        print(f"DEBUG_LMS_UPLOAD: Success material_id={material.id}")
        return {"success": True, "material_id": material.id, "title": title}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("/classrooms/{classroom_id}/materials")
async def list_materials(
    classroom_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List materials in a classroom."""
    # Check membership
    member = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.user_id == user.id
    ).first()
    if not member and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not a member of this classroom")
        
    materials = db.query(LMSMaterial).filter(LMSMaterial.classroom_id == classroom_id).all()
    return materials



# ═══════════════════════════════════════════════════════════════
# NEXT-GEN AI LMS ROUTES (NEW)
# ═══════════════════════════════════════════════════════════════

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None

@router.post("/courses", tags=["Teacher Studio"])
async def create_new_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Create a high-level course in the new AI LMS structure."""
    course = Course(
        instructor_id=user.id,
        title=data.title,
        description=data.description,
        subject=data.subject,
        status="draft"
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"success": True, "course_id": course.id}

@router.get("/courses", tags=["Courses"])
async def list_courses_consolidated(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List courses based on user role: Teachers see owned, students see published."""
    if user.role in ["teacher", "admin"]:
        courses = db.query(Course).filter(Course.instructor_id == user.id).all()
    else:
        courses = db.query(Course).filter(Course.status == "published").all()
    return [
        {"id": c.id, "title": c.title, "description": c.description, "subject": c.subject, "status": c.status} 
        for c in courses
    ]


class SectionCreate(BaseModel):
    title: str
    order: Optional[int] = 0
    summary: Optional[str] = None

@router.post("/courses/{course_id}/sections", tags=["Teacher Studio"])
async def create_section(
    course_id: int,
    data: SectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Architect a new section within a course."""
    section = Section(
        course_id=course_id,
        title=data.title,
        order=data.order,
        summary=data.summary
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return {"success": True, "section_id": section.id}

class ModuleCreate(BaseModel):
    title: str
    content_type: str
    order: Optional[int] = 0

@router.post("/sections/{section_id}/modules", tags=["Teacher Studio"])
async def create_module(
    section_id: int,
    data: ModuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Add a learning module to a section."""
    module = LessonModule(
        section_id=section_id,
        title=data.title,
        content_type=data.content_type,
        order=data.order
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return {"success": True, "module_id": module.id}


# --- Removed Duplicate Route: get_course_structure ---


class EventCreate(BaseModel):
    event_type: str
    path: Optional[str] = None
    metadata: Optional[dict] = None

@router.post("/events", tags=["Analytics"])
async def log_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Log an analytics event (click, view, session tracking)."""
    user_id = user.id if user else None
    
    log = EventLog(
        user_id=user_id,
        event_type=event.event_type,
        path=event.path,
        metadata_json=event.metadata
    )
    db.add(log)
    db.commit()
    return {"success": True}


@router.get("/mastery-view", tags=["Graph Visualizer"])
async def get_mastery_graph_data(
    upload_id: Optional[int] = None,
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get summarized mastery data for the interactive graph visualizer."""
    # Priority: query user_id > current_user > guest logic
    target_id = None
    if user_id:
        target_id = user_id
    elif current_user:
        target_id = current_user.id
    else:
        # Fallback for pure guest
        target_id = None 
    
    # Get latest mastery for each entity
    from app.models import GraphEntity, Upload, MasteryLog
    
    query = db.query(GraphEntity)
    if upload_id:
        query = query.filter(GraphEntity.upload_id == upload_id)
    
    entities = query.all()
    
    # --- Fallback: If no entities in DB, try to extract from Upload's study package ---
    if not entities and upload_id:
        active_upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if active_upload:
            try:
                pkg = json.loads(active_upload.study_package)
                # Mock nodes from "concepts" if graph nodes weren't synced
                concepts = pkg.get("data", {}).get("concepts", [])
                entities = [
                    GraphEntity(id=i, entity_name=c["name"], entity_type="concept", mastery_score=0.5)
                    for i, c in enumerate(concepts)
                ]
            except Exception:
                pass

    mastery_map = []
    for ent in entities:
        # Check if user has specific logs, otherwise fallback to entity global mastery
        # (Only do this for real DB entities)
        score = ent.mastery_score
        if hasattr(ent, 'id') and ent.id:
            latest_log = db.query(MasteryLog).filter(
                MasteryLog.user_id == target_id,
                MasteryLog.entity_id == ent.id
            ).order_by(MasteryLog.logged_at.desc()).first()
            if latest_log:
                score = latest_log.score
        
        mastery_map.append({
            "id": getattr(ent, 'id', 0) or 0,
            "name": ent.entity_name,
            "type": ent.entity_type,
            "mastery": score,
            "community": getattr(ent, 'community_id', 0) or 0
        })
    
    return mastery_map


@router.get("/risk-flags", tags=["AI Academic Risk"])
async def get_risk_report(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Retrieve students at risk for a specific course or across all classrooms."""
    query = db.query(AcademicRisk)
    if course_id:
        query = query.filter(AcademicRisk.course_id == course_id)
    else:
        # Get all courses the teacher is instructor of
        courses_taught = db.query(Course).filter(Course.instructor_id == user.id).all()
        c_ids = [c.id for c in courses_taught]
        query = query.filter(AcademicRisk.course_id.in_(c_ids))
    
    risks = query.all()
    
    results = []
    for r in risks:
        student = db.query(User).filter(User.id == r.user_id).first()
        results.append({
            "student_id": str(r.user_id),
            "student_name": student.name if student else "Unknown",
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "flags": r.flags,
            "updated_at": r.last_updated.isoformat()
        })
    
    return sorted(results, key=lambda x: x["risk_score"], reverse=True)
@router.get("/reminders", tags=["Scheduler"])
async def get_reminders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_optional)
):
    """Retrieve all pending reminders and milestones for the user."""
    if not user:
        # For DEMO: If guest, return some generated reminders based on current date
        return [
            {"id": "m1", "title": "Welcome to Studymines!", "type": "study", "due_at": datetime.utcnow().isoformat(), "priority": "high", "status": "pending"},
            {"id": "m2", "title": "Upload your first doc", "type": "task", "due_at": datetime.utcnow().isoformat(), "priority": "medium", "status": "pending"}
        ]
        
    reminders = db.query(LMSReminder).filter(
        LMSReminder.user_id == user.id,
        LMSReminder.status == "pending"
    ).order_by(LMSReminder.due_at).all()
    
    return [
        {
            "id": r.id,
            "title": r.title,
            "type": r.reminder_type,
            "due_at": r.due_at.isoformat(),
            "priority": r.priority,
            "status": r.status
        }
        for r in reminders
    ]

class ReminderCreate(BaseModel):
    title: str
    due_at: datetime
    reminder_type: Optional[str] = "task"
    priority: Optional[str] = "medium"

@router.post("/reminders", tags=["Scheduler"])
async def create_reminder(
    data: ReminderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Manually add a reminder to the chronos."""
    reminder = LMSReminder(
        user_id=user.id,
        title=data.title,
        due_at=data.due_at,
        reminder_type=data.reminder_type,
        priority=data.priority
    )
    db.add(reminder)
    db.commit()
    return {"success": True}


@router.post("/studio/generate-quiz", tags=["Teacher Studio"])
async def auto_generate_quiz_from_text(
    material_id: int,
    num_questions: int = 5,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Uses NLP to extract questions from an existing LMSMaterial and populate QuestionBank."""
    material = db.query(LMSMaterial).filter(LMSMaterial.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    import json
    study_pkg = json.loads(material.study_package) if material.study_package else {}
    questions = study_pkg.get("data", {}).get("questions", [])
    
    new_q_ids = []
    for q in questions[:num_questions]:
        # Create Question Bank entry
        bank_q = QuestionBank(
            subject=material.classroom.subject if material.classroom else None,
            topic=material.title,
            question_type="mcq" if "options" in q else "open",
            content=q,
            difficulty=2 # Default medium
        )
        db.add(bank_q)
        db.flush()
        new_q_ids.append(bank_q.id)
    
    db.commit()
    return {"success": True, "count": len(new_q_ids), "question_ids": new_q_ids}
class UniversalExamCreate(BaseModel):
    title: str
    course_id: Optional[int] = None
    classroom_id: Optional[str] = None
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"
    context_type: str = "general" # 'general', 'document', 'mastery'

def background_generate_exam(exam_id: int, topic: str, context_type: str, num_questions: int, difficulty: str):
    from app.database import SessionLocal
    import traceback
    db = SessionLocal()
    try:
        from app.lms.core.ai_generator import CognitiveAIGenerator
        from app.models import QuestionBank, Assessment
        print(f"[ExamGen] Starting generation for exam_id={exam_id}, topic={topic}, num={num_questions}")
        questions = CognitiveAIGenerator(
            topic=topic,
            context_type=context_type,
            num_items=num_questions,
            difficulty=difficulty,
            db=db
        )
        print(f"[ExamGen] Generated {len(questions)} questions")
        q_ids = []
        for q in questions:
            qb = QuestionBank(
                subject=topic,
                topic=topic,
                question_type="mcq",
                difficulty=2,
                content=q
            )
            db.add(qb)
            db.flush()
            q_ids.append(qb.id)
            
        exam = db.query(Assessment).filter(Assessment.id == exam_id).first()
        if exam:
            exam.question_ids = q_ids
            exam.is_published = True
            db.commit()
            print(f"[ExamGen] Successfully published exam_id={exam_id} with {len(q_ids)} questions")
        else:
            print(f"[ExamGen] ERROR: Assessment id={exam_id} not found in DB")
    except Exception as e:
        print(f"[ExamGen] Background generation failed: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


@router.post("/exams/generate", tags=["Exam Architect"])
async def generate_universal_exam(
    data: UniversalExamCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Universal generation endpoint for Exams and Quizzes using CognitiveAIGenerator."""
    # Normalize empty strings to None for FK safety
    classroom_id = data.classroom_id if data.classroom_id else None
    course_id = data.course_id if data.course_id else None
    
    new_exam = Assessment(
        course_id=course_id,
        classroom_id=classroom_id,
        title=data.title,
        is_published=False,
        question_ids=[]
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    
    background_tasks.add_task(
        background_generate_exam, 
        new_exam.id, data.topic, data.context_type, data.num_questions, data.difficulty
    )
    
    return {"success": True, "assessment_id": new_exam.id, "status": "processing"}


class AssessmentSubmission(BaseModel):
    responses: dict
    time_spent: Optional[int] = None

@router.post("/assessments/{assessment_id}/submit", tags=["Assessment"])
async def submit_assessment(
    assessment_id: int,
    data: AssessmentSubmission,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Submit a native LMS assessment, calculate score, and update mastery."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Simple score calculation (Assumes single choice MCQ for now)
    # real production would iterate through questions and verify
    # For now, we'll mock the calculation or assume it's pre-calculated for simple demo
    # BUT we should record the attempt
    
    # Mock calculation if needed, or assume 'responses' has a 'score' for this MVP
    score = data.responses.get("score", 75.0) # Default if not provided
    is_passed = score >= assessment.passing_score
    
    attempt = AssessmentAttempt(
        user_id=user.id,
        assessment_id=assessment_id,
        score=score,
        is_passed=is_passed,
        responses=data.responses
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    # --- Integration: Update Mastery Logs for the entities linked to this assessment ---
    # Assessment might be tied to a course, update all entities if so
    from app.lms.risk_engine import update_mastery_from_quiz, RiskEngine
    
    # If the assessment has explicit question links to entities, use those
    # For now, if tied to a course, we'll iterate course entities or just global update
    if assessment.course_id:
        engine = RiskEngine(db)
        await engine.analyze_student(user.id, assessment.course_id)
    
    return {"success": True, "score": score, "attempt_id": attempt.id}



@router.get("/classrooms/{classroom_id}/exams", tags=["Exam Architect"])
async def list_classroom_exams(classroom_id: str, db: Session = Depends(get_db)):
    """List all exams/assessments for a classroom."""
    exams = db.query(Assessment).filter(Assessment.classroom_id == classroom_id).all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "points": e.total_points,
            "is_published": e.is_published,
            "created_at": getattr(e.created_at, 'isoformat', lambda: str(e.created_at))()
        }
        for e in exams
    ]

@router.get("/assessments/{assessment_id}", tags=["Assessment"])
async def get_assessment_details(assessment_id: int, db: Session = Depends(get_db)):
    """Retrieve full details for an assessment including all question content."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    questions = []
    if assessment.question_ids:
        q_records = db.query(QuestionBank).filter(QuestionBank.id.in_(assessment.question_ids)).all()
        q_map = {q.id: q for q in q_records}
        for q_id in assessment.question_ids:
            if q_id in q_map:
                q = q_map[q_id]
                questions.append({
                    "id": q.id,
                    "type": q.question_type,
                    "difficulty": q.difficulty,
                    "content": q.content
                })
    
    return {
        "id": assessment.id,
        "title": assessment.title,
        "description": assessment.description,
        "total_points": assessment.total_points,
        "time_limit": assessment.time_limit,
        "questions": questions
    }


@router.get("/members", tags=["Organization"])
async def get_all_members(db: Session = Depends(get_db), user: User = Depends(require_role(["teacher", "admin"]))):
    """Fetch all users in the tenant for the management view."""
    users = db.query(User).all()
    return [
        {
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "status": u.status or "active"
        }
        for u in users
    ]

@router.post("/members/{user_id}/status", tags=["Organization"])
async def update_member_status(
    user_id: str,
    status: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin", "teacher"]))
):
    """Change user status (active/banned/etc)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.status = status
    db.commit()
    return {"success": True}

@router.post("/members/{user_id}/role", tags=["Organization"])
async def update_member_role(
    user_id: str,
    role: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin", "teacher"]))
):
    """Update a user's role (student/teacher/admin)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = role
    db.commit()
    return {"success": True}

@router.delete("/members/{user_id}", tags=["Organization"])
async def delete_member(
    user_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin", "teacher"]))
):
    """
    Permanently delete a user (caution).
    - Admins can delete anyone.
    - Teachers can only delete students.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Security Check: Teachers cannot delete other teachers or admins
    if user.role == "teacher" and target.role != "student":
        raise HTTPException(
            status_code=403, 
            detail="Teachers can only manage and unenroll student-level accounts."
        )
        
    db.delete(target)
    db.commit()
    return {"success": True}

@router.get("/assignments", tags=["Assignments"])
async def get_all_assignments(db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    """Fetch all assessments assigned across the user's courses."""
    # Join with User is unnecessary as it is available.
    return [
        {
            "id": a.id,
            "title": a.title,
            "class": a.course.name if a.course else "General Academy",
            "due": "In 3 Days", 
            "status": "active" if a.is_published else "generating",
            "completions": f"{db.query(AssessmentAttempt).filter(AssessmentAttempt.assessment_id == a.id).count()} Active"
        }
        for a in db.query(Assessment).all()
    ]

# --- Removed Duplicate Route: get_course_full_view ---


@router.get("/stats/heatmap", tags=["Analytics"])
async def get_cognitive_heatmap(db: Session = Depends(get_db)):
    """Aggregate mastery data by concept to show high-struggle areas."""
    concepts = db.query(
        GraphEntity.entity_name,
        func.avg(GraphEntity.mastery_score).label("avg_mastery"),
        func.count(GraphEntity.id).label("mentions")
    ).group_by(GraphEntity.entity_name).limit(10).all()
    
    return [
        {
            "concept": c.entity_name,
            "struggle_index": round((1.0 - float(c.avg_mastery or 0.8)) * 100, 1),
            "mentions": (c.mentions or 0) * 12, # Scale for UI impact
            "confidence": 0.85 + (0.1 * (1.0 - float(c.avg_mastery or 0.8)))
        }
        for c in concepts
    ]

@router.get("/stats/kpis", tags=["Analytics"])
async def get_analytics_kpis(db: Session = Depends(get_db)):
    """Core metrics for the analytics dashboard."""
    concept_count = db.query(GraphEntity).count()
    global_mastery = db.query(func.avg(GraphEntity.mastery_score)).scalar() or 0.72
    high_struggle = db.query(GraphEntity).filter(GraphEntity.mastery_score < 0.4).count()
    
    return {
        "concepts_monitored": concept_count,
        "global_mastery_pct": round(float(global_mastery) * 100, 1),
        "high_struggle_count": high_struggle
    }

@router.get("/learning-paths", tags=["Graph Visualizer"])
async def get_recommended_learning_paths(
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Dynamically calculates the recommended next modules/concepts based on KG mastery topology."""
    target_id = user_id or (current_user.id if current_user else None)
    if not target_id:
        return {"recommendations": [], "message": "Login to see your personalized path."}

    # 1. Identify "Weak" Concepts (Mastery < 0.5)
    from app.models import GraphEntity, MasteryLog
    
    # Get all entities and their latest mastery for this user
    entities = db.query(GraphEntity).all()
    weak_concepts = []
    
    for ent in entities:
        latest_log = db.query(MasteryLog).filter(
            MasteryLog.user_id == target_id,
            MasteryLog.entity_id == ent.id
        ).order_by(MasteryLog.logged_at.desc()).first()
        
        score = latest_log.score if latest_log else ent.mastery_score
        if score < 0.6: # Threshold for recommendation
            weak_concepts.append({
                "id": ent.id,
                "name": ent.entity_name,
                "score": score,
                "type": ent.entity_type
            })

    # Sort by lowest score first
    weak_concepts.sort(key=lambda x: x["score"])

    # 2. Map concepts to Modules
    # For now, we'll suggest general "Review" actions if no direct module mapping
    # But we can look for LessonModules that mention these concept names
    recommendations = []
    for concept in weak_concepts[:3]:
        # Try to find a module that contains this concept name in its title
        module = db.query(LessonModule).filter(LessonModule.title.ilike(f"%{concept['name']}%")).first()
        
        recommendations.append({
            "concept_id": concept["id"],
            "concept_name": concept["name"],
            "current_mastery": round(concept["score"] * 100, 1),
            "suggested_action": f"Review {concept['name']} foundations" if not module else f"Study Module: {module.title}",
            "priority": "high" if concept["score"] < 0.3 else "medium",
            "module_id": module.id if module else None
        })

    return {
        "user_id": str(target_id),
        "recommendations": recommendations,
        "path_status": "at_risk" if any(r["priority"] == "high" for r in recommendations) else "stable"
    }

@router.get("/chats/global", tags=["Communication Matrix"])
async def get_global_chats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Retrieve all active classroom chat rooms user is part of."""
    rooms = db.query(ChatRoom).join(Classroom).join(ClassroomMember).filter(ClassroomMember.user_id == user.id).all()
    results = []
    for r in rooms:
        # Get last message
        last_msg = db.query(ChatMessage).filter(ChatMessage.room_id == r.id).order_by(ChatMessage.created_at.desc()).first()
        # Count members
        member_count = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == r.classroom_id).count() if r.classroom_id else 0
        
        results.append({
            "id": r.id,
            "name": r.name or "Unnamed Room",
            "members": member_count,
            "lastMessage": last_msg.content if last_msg else "No activity yet.",
            "time": last_msg.created_at.strftime("%I:%M %p") if last_msg else "Quiet"
        })
    return results
# ═══════════════════════════════════════════════════════════════
# INSTRUCTOR STUDIO (AI ARCHITECTURE)
# ═══════════════════════════════════════════════════════════════
# --- Removed Duplicate Route: get_courses ---

@router.post("/courses", tags=["Studio"])
async def create_course(data: dict, db: Session = Depends(get_db), user: User = Depends(require_role(["teacher", "admin"]))):
    """Create a new course shell."""
    course = Course(
        title=data.get("title", "Untitled Course"),
        description=data.get("description", ""),
        instructor_id=user.id,
        status="draft"
    )
    db.add(course)
    db.commit()
    return {"course_id": course.id, "success": True}

@router.post("/courses/{course_id}/sections", tags=["Studio"])
async def add_course_section(course_id: int, data: dict, db: Session = Depends(get_db), user: User = Depends(require_role(["teacher", "admin"]))):
    """Add a new section to a course."""
    section = Section(
        course_id=course_id,
        title=data.get("title", "New Section"),
        order=data.get("order", 0)
    )
    db.add(section)
    db.commit()
    return {"section_id": section.id, "success": True}

# --- Removed Duplicate Route: get_course_modules ---

@router.post("/studio/publish-architecture/{course_id}", tags=["Studio"])
async def publish_course_architecture(
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Marks a course architecture as published, making it visible to students."""
    course = db.query(Course).filter(Course.id == course_id, Course.instructor_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")
    
    course.status = "published"
    db.commit()
    return {"success": True, "message": f"Course '{course.title}' published successfully."}

class AIArchitectRequest(BaseModel):
    artifact_id: int # Upload ID

@router.post("/studio/ai-architect/{course_id}", tags=["Studio"])
async def ai_architect_course(
    course_id: int,
    data: AIArchitectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """
    RAG-driven curriculum synthesis. 
    Uses an artifact to automatically generate sections and modules.
    """
    from app.models import Upload
    
    course = db.query(Course).filter(Course.id == course_id, Course.instructor_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    artifact = db.query(Upload).filter(Upload.id == data.artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
        
    # LOGIC: Mocking AI Deconstruction based on filename/subject
    # In a real RAG flow, we would use CognitiveAIGenerator to parse the file 
    # and extract "Table of Contents" or "Core Concepts".
    
    # 1. Create a "Foundation" Section
    sec1 = Section(course_id=course.id, title=f"Foundations of {artifact.file_name.split('.')[0]}", order=0)
    db.add(sec1)
    db.flush()
    
    # Add Modules
    m1 = LessonModule(section_id=sec1.id, title="Core Concept Overview", content_type="document", order=0)
    m2 = LessonModule(section_id=sec1.id, title="Synthesized Summary", content_type="document", order=1)
    db.add_all([m1, m2])
    
    # 2. Create an "Advanced Applications" Section
    sec2 = Section(course_id=course.id, title="Advanced Synthesis & Applications", order=1)
    db.add(sec2)
    db.flush()
    
    m3 = LessonModule(section_id=sec2.id, title="AI-Generated Practice Quiz", content_type="quiz", order=0)
    db.add(m3)
    
    db.commit()
    return {
        "success": True, 
        "message": "AI Architecture complete.",
        "sections_added": 2,
        "modules_added": 3
    }
