import secrets
import shutil
import os
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import User
from app.lms.models.classroom import Classroom, ClassroomMember
from app.lms.models.material import LMSMaterial
from app.lms.models.chat import ChatRoom, ChatMessage

from app.lms.auth import get_current_user, require_role

router = APIRouter(prefix="/lms", tags=["LMS Core"])

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

    # Convert to schema and manual field additions
    res_dict = {column.name: getattr(classroom, column.name) for column in classroom.__table__.columns}
    res_dict["member_count"] = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).count()
    res_dict["chat_room_id"] = chat_room.id if chat_room else None
    
    return res_dict
    # Check membership
    member = db.query(ClassroomMember).filter(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.user_id == user.id
    ).first()
    if not member and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not a member of this classroom")
    
    classroom.member_count = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).count()
    
    # Attach ChatRoom id
    chat_room = db.query(ChatRoom).filter(ChatRoom.classroom_id == classroom_id).first()
    res = {column.name: getattr(classroom, column.name) for column in classroom.__table__.columns}
    res["member_count"] = classroom.member_count
    res["chat_room_id"] = chat_room.id if chat_room else None
    
    return res

@router.post("/materials/upload")
async def upload_material(
    classroom_id: str = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """Upload material to a classroom and save locally."""
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
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Create Record
    material = LMSMaterial(
        classroom_id=classroom_id,
        title=title,
        description=description,
        file_path=file_path,
        file_type=file.content_type,
        uploaded_by=user.id,
        status="ready"
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return {"success": True, "material_id": material.id, "file_path": file_path}

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

@router.get("/members")
async def list_global_members(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """List all users in the system (for Members dashboard)."""
    users = db.query(User).all()
    # Mask password_hash
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "status": u.status} for u in users]

@router.get("/chats/global")
async def list_global_chats(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """List all global chat rooms and their summary."""
    # For now, just return classroom chat rooms user is part of
    rooms = db.query(ChatRoom).join(Classroom).join(ClassroomMember).filter(ClassroomMember.user_id == user.id).all()
    results = []
    for r in rooms:
        member_count = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == r.classroom_id).count()
        results.append({
            "id": r.id, 
            "name": r.name, 
            "members": member_count,
            "lastMessage": "Welcome to the discussion", 
            "time": "Today"
        })
    return results

@router.get("/materials/global")
async def list_global_materials(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """List all materials uploaded by this teacher across all classes."""
    materials = db.query(LMSMaterial).join(Classroom).filter(LMSMaterial.uploaded_by == user.id).all()
    results = []
    for m in materials:
        results.append({
            "id": m.id,
            "title": m.title,
            "class": m.classroom.code if m.classroom else "N/A",
            "date": m.created_at.strftime("%Y-%m-%d"),
            "status": m.status,
            "uses": 0
        })
    return results
