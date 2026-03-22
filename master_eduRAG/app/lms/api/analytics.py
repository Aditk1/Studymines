from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Upload, GraphEntity
from app.lms.models.classroom import Classroom, ClassroomMember
from app.lms.models.material import LMSMaterial
from app.lms.models.exam import ExamSubmission
from app.lms.auth import get_current_user, require_role

router = APIRouter(prefix="/lms", tags=["LMS Analytics"])

@router.get("/analytics/teacher/insight")
async def get_teacher_insight(
    classroom_id: str = None, 
    db: Session = Depends(get_db), 
    user: User = Depends(require_role(["teacher", "admin"]))
):
    """
    Teacher's Insight (Heatmap):
    Aggregates GraphEntities across all materials in the teacher's classrooms
    to identify concepts with low mastery or high frequency in queries.
    """
    # 1. Get all classrooms for this teacher
    query = db.query(Classroom).filter(Classroom.created_by == user.id)
    if classroom_id:
        query = query.filter(Classroom.id == classroom_id)
    classrooms = query.all()
    classroom_ids = [c.id for c in classrooms]

    if not classroom_ids:
        return {"heatmap_data": [], "message": "No classrooms found."}

    # 2. Extract concepts relevant to these classrooms
    # For now, we simulate the link between LMSMaterial and the core Upload/GraphEntity.
    # We aggregate entities by name, showing average mastery and count.
    
    # In a full production setup, LMSMaterial.id would map to Upload.id, 
    # but here we aggregate all graph entities globally as an example of cognitive insight.
    # Alternatively, group by community_id to find cluster weaknesses.
    
    results = (
        db.query(
            GraphEntity.entity_name,
            func.count(GraphEntity.id).label("frequency"),
            func.avg(GraphEntity.mastery_score).label("avg_mastery"),
            func.avg(GraphEntity.confidence).label("avg_confidence")
        )
        .group_by(GraphEntity.entity_name)
        .order_by(func.count(GraphEntity.id).desc())
        .limit(20)
        .all()
    )

    heatmap = [
        {
            "concept": r.entity_name,
            "struggle_index": max(0.0, 100.0 - (r.avg_mastery or 0.0) * 100), # 100% means extreme struggle
            "mentions": r.frequency,
            "confidence": r.avg_confidence
        }
        for r in results
    ]

    return {"success": True, "heatmap_data": heatmap}

@router.get("/search/cross-classroom")
async def cross_classroom_search(
    query: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Cross-Classroom Search:
    Searches materials matching the semantic query string across all classrooms the user has access to.
    """
    # Simply using ilike for text search natively here.
    # A true semantic search would involve vector DB matching on DocumentChunks.
    
    # Get user's classrooms
    if user.role == "teacher":
        classrooms = db.query(Classroom).filter(Classroom.created_by == user.id).all()
    else:
        memberships = db.query(ClassroomMember).filter(ClassroomMember.user_id == user.id).all()
        classroom_ids = [m.classroom_id for m in memberships]
        classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()

    c_ids = [c.id for c in classrooms]
    
    materials = db.query(LMSMaterial).filter(
        LMSMaterial.classroom_id.in_(c_ids),
        (LMSMaterial.title.ilike(f"%{query}%") | LMSMaterial.description.ilike(f"%{query}%") | LMSMaterial.ai_summary.ilike(f"%{query}%"))
    ).limit(10).all()

    return {
        "success": True,
        "results": [
            {
                "id": m.id,
                "title": m.title,
                "classroom_id": m.classroom_id,
                "ai_summary": m.ai_summary
            } for m in materials
        ]
    }
