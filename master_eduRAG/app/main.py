"""
master_eduRAG — Unified FastAPI Application
Studymines (Adaptive Learning) × RLM-GraphRAG (Cognitive Core)

Endpoints:
  ── Studymines ──
  POST /api/v1/upload/document    Upload & process document → study package
  POST /api/v1/upload/image       Upload & process image    → study package
  GET  /api/v1/users/{id}         User dashboard
  GET  /api/v1/leaderboard        Leaderboard
  POST /api/v1/auth/signup        Register
  POST /api/v1/auth/login         Login
  POST /api/v1/performance        Record quiz score

  ── RLM-GraphRAG ──
  POST /api/v1/graph/query        Multi-hop QA over Knowledge Graph
  GET  /api/v1/graph/view/{id}    View graph metadata for an upload
  GET  /api/v1/graph/entities     List entities for an upload
"""

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import os, tempfile, json, uuid, shutil
from typing import Optional

from app.database import init_db, get_db
from app.models import User, Upload, Performance, GraphEntity
from app.parsers.document_parser import parse_document
from app.vision.image_preprocessor import ImagePreprocessor
from app.vision.vision_extractor import extract_from_image
from app.preprocessing import preprocess_text
from app.segregation import segregate_content
from app.chunking import chunk_and_process
from app.config import MAX_FILE_SIZE, MAX_IMAGE_SIZE, ALLOWED_DOCUMENT_TYPES, ALLOWED_IMAGE_TYPES

# ── App Factory ────────────────────────────────────────────────

app = FastAPI(
    title="master_eduRAG — Cognitive Learning System",
    description="Studymines × RLM-GraphRAG: Adaptive study packages with multi-hop graph reasoning.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("✓ Database initialised successfully")
    except Exception as e:
        print(f"⚠ DB init warning: {e}")


# ═══════════════════════════════════════════════════════════════
# Root
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "name": "master_eduRAG",
        "version": "1.0.0",
        "status": "running",
        "modules": {
            "studymines": "active",
            "rlm_graphrag": "active",
        },
        "endpoints": {
            "upload_document": "/api/v1/upload/document",
            "upload_image": "/api/v1/upload/image",
            "graph_query": "/api/v1/graph/query",
            "graph_view": "/api/v1/graph/view/{upload_id}",
            "graph_entities": "/api/v1/graph/entities?upload_id=...",
            "user_dashboard": "/api/v1/users/{user_id}",
            "leaderboard": "/api/v1/leaderboard",
        },
    }


# ═══════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/auth/signup")
async def signup(
    name: str = Form(...), email: str = Form(...),
    password: str = Form(...), student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return JSONResponse(status_code=400, content={"error": "Email already registered"})
    user = User(name=name, email=email, password_hash=password, student_level=student_level)
    db.add(user); db.commit(); db.refresh(user)
    return {"success": True, "user": {"id": user.id, "name": user.name, "email": user.email, "student_level": user.student_level}}


@app.post("/api/v1/auth/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or user.password_hash != password:
        return JSONResponse(status_code=401, content={"error": "Invalid email or password"})
    return {"success": True, "user": {"id": user.id, "name": user.name, "email": user.email, "student_level": user.student_level}}


@app.post("/api/v1/users")
async def create_user(name: str = Form(...), email: str = Form(...), student_level: str = Form("undergraduate"), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return {"id": existing.id, "name": existing.name, "email": existing.email, "student_level": existing.student_level, "message": "User already exists"}
    user = User(name=name, email=email, student_level=student_level)
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "student_level": user.student_level, "message": "User created"}


@app.get("/api/v1/users/guest/{username}")
async def get_or_create_guest(username: str, db: Session = Depends(get_db)):
    email = f"{username}@guest.local"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=username, email=email, student_level="undergraduate")
        db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "student_level": user.student_level}


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _resolve_user(user_id: str, db: Session, student_level: str = "undergraduate") -> User:
    if user_id.isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()
    else:
        email = f"{user_id}@guest.local"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(name=user_id, email=email, student_level=student_level)
            db.add(user); db.commit(); db.refresh(user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ═══════════════════════════════════════════════════════════════
# Document Upload  (Studymines + RAG Bridge)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db),
):
    try:
        user = _resolve_user(user_id, db, student_level)
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        file_ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if file_ext not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported type: {file_ext}")

        # Generate permanent storage path
        save_dir = "data/uploads"
        os.makedirs(save_dir, exist_ok=True)
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        permanent_path = os.path.join(save_dir, unique_filename)

        with open(permanent_path, "wb") as f:
            f.write(content)

        try:
            parsed = parse_document(permanent_path)
            text = preprocess_text(parsed["text"])
            segregation = segregate_content(text, subject, topic, file.filename)

            study_package = await chunk_and_process(
                text, student_level,
                segregation.get("subject"), segregation.get("topic"),
                source_name=file.filename,
            )

            # Persist
            graph_meta = study_package.get("graph_metadata", {})
            upload_rec = Upload(
                user_id=user.id, file_name=file.filename,
                file_type=parsed["metadata"].get("file_type", "unknown"),
                subject=segregation.get("subject"), topic=segregation.get("topic"),
                file_path=permanent_path,
                study_package=json.dumps(study_package),
                graph_path=graph_meta.get("graph_path"),
                graph_triples_count=graph_meta.get("triples_count"),
                graph_confidence=graph_meta.get("extraction_confidence"),
            )
            db.add(upload_rec); db.commit()

            return {"success": True, "upload_id": upload_rec.id, "file_name": file.filename,
                    "segregation": segregation, "study_package": study_package}
        except Exception:
            # Clean up on process failure if needed
            # if os.path.exists(permanent_path): os.unlink(permanent_path)
            raise

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


# ═══════════════════════════════════════════════════════════════
# Image Upload  (Studymines Vision + RAG Bridge)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db),
):
    try:
        user = _resolve_user(user_id, db, student_level)
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="Image too large")

        file_ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if file_ext not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported image type: {file_ext}")

        save_dir = "data/uploads"
        os.makedirs(save_dir, exist_ok=True)
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        permanent_path = os.path.join(save_dir, unique_filename)

        with open(permanent_path, "wb") as f:
            f.write(content)

        try:
            ImagePreprocessor.preprocess(permanent_path)
            extraction = extract_from_image(permanent_path)

            if not extraction.get("extracted_text"):
                raise ValueError("Failed to extract text from image.")

            legibility_warning = None
            if extraction.get("confidence") == "low":
                legibility_warning = f"Low confidence. Issues: {extraction.get('issues', 'poor quality')}"

            text = preprocess_text(extraction["extracted_text"])
            segregation = segregate_content(text, subject, topic, file.filename)

            study_package = await chunk_and_process(
                text, student_level,
                segregation.get("subject"), segregation.get("topic"),
                source_name=file.filename,
            )

            graph_meta = study_package.get("graph_metadata", {})
            upload_rec = Upload(
                user_id=user.id, file_name=file.filename, file_type="image",
                subject=segregation.get("subject"), topic=segregation.get("topic"),
                file_path=permanent_path,
                study_package=json.dumps(study_package),
                graph_path=graph_meta.get("graph_path"),
                graph_triples_count=graph_meta.get("triples_count"),
                graph_confidence=graph_meta.get("extraction_confidence"),
            )
            db.add(upload_rec); db.commit()

            resp = {"success": True, "upload_id": upload_rec.id, "file_name": file.filename,
                    "extraction_confidence": extraction.get("confidence"),
                    "segregation": segregation, "study_package": study_package}
            if legibility_warning:
                resp["legibility_warning"] = legibility_warning
            return resp
        except Exception:
            raise

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


# ═══════════════════════════════════════════════════════════════
# Graph Endpoints  (NEW — RLM-GraphRAG)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/graph/query")
async def graph_query(
    question: str = Form(...),
    upload_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """Multi-hop question answering over the Knowledge Graph."""
    from app.bridge import RAGBridge

    graph_path = None
    if upload_id:
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if upload:
            graph_path = upload.graph_path

    bridge = RAGBridge()
    result = await bridge.query_graph(question, graph_path)
    return result


@app.post("/api/v1/graph/chat")
async def graph_chat(
    message: str = Form(...),
    upload_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """Alias for graph_query specifically intended for Chatbot integration."""
    return await graph_query(question=message, upload_id=upload_id, db=db)


@app.get("/api/v1/graph/view/{upload_id}")
async def graph_view(upload_id: int, db: Session = Depends(get_db)):
    """Return graph metadata for a specific upload."""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    return {
        "upload_id": upload.id,
        "file_name": upload.file_name,
        "graph_path": upload.graph_path,
        "triples_count": upload.graph_triples_count,
        "extraction_confidence": upload.graph_confidence,
    }


@app.get("/api/v1/graph/entities")
async def graph_entities(upload_id: int, db: Session = Depends(get_db)):
    """List entities extracted for a specific upload."""
    entities = db.query(GraphEntity).filter(GraphEntity.upload_id == upload_id).all()
    return [
        {
            "id": e.id, "name": e.entity_name, "type": e.entity_type,
            "community": e.community_id, "confidence": e.confidence,
            "mastery": e.mastery_score,
        }
        for e in entities
    ]


# ═══════════════════════════════════════════════════════════════
# Dashboard / Leaderboard / Performance
# ═══════════════════════════════════════════════════════════════

@app.get("/api/v1/users/{user_id}")
async def get_user_dashboard(user_id: str, db: Session = Depends(get_db)):
    user = _resolve_user(user_id, db)
    uploads = db.query(Upload).filter(Upload.user_id == user.id).all()
    performance = db.query(Performance).filter(Performance.user_id == user.id).all()

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email, "student_level": user.student_level},
        "uploads": [
            {"id": u.id, "file_name": u.file_name, "subject": u.subject, "topic": u.topic,
             "graph_path": u.graph_path, "created_at": u.uploaded_at.isoformat()}
            for u in uploads
        ],
        "uploads_count": len(uploads),
        "performance": {
            "avg_score": sum(p.score for p in performance) / len(performance) if performance else 0,
            "total_scores": len(performance),
        },
    }


@app.get("/api/v1/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    results = (
        db.query(User.id, User.name, User.email,
                 func.count(Upload.id).label("uploads_count"),
                 func.coalesce(func.avg(Performance.score), 0).label("avg_score"))
        .outerjoin(Upload, User.id == Upload.user_id)
        .outerjoin(Performance, User.id == Performance.user_id)
        .group_by(User.id, User.name, User.email)
        .order_by(func.coalesce(func.avg(Performance.score), 0).desc(),
                  func.count(Upload.id).desc())
        .all()
    )
    return [
        {"rank": i + 1, "user_id": r.id, "name": r.name, "email": r.email,
         "uploads_count": int(r.uploads_count or 0), "score": float(r.avg_score or 0)}
        for i, r in enumerate(results)
    ]


@app.get("/api/v1/uploads/{upload_id}/file")
async def get_upload_file(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload or not upload.file_path or not os.path.exists(upload.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(upload.file_path, filename=upload.file_name)


@app.get("/api/v1/uploads/{upload_id}")
async def get_upload(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    pkg = {}
    if upload.study_package:
        try:
            pkg = json.loads(upload.study_package)
        except Exception:
            pkg = {"error": "Could not parse study package"}
    return {"success": True, "id": upload.id, "file_name": upload.file_name,
            "subject": upload.subject, "topic": upload.topic, "study_package": pkg}


@app.post("/api/v1/performance")
async def record_performance(
    upload_id: int = Form(...), user_id: str = Form(...),
    score: float = Form(...), notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    user = _resolve_user(user_id, db)
    perf = Performance(user_id=user.id, upload_id=upload_id, score=score, notes=notes)
    db.add(perf); db.commit(); db.refresh(perf)
    return {"success": True, "performance_id": perf.id}


@app.get("/api/v1/research/metrics")
async def research_metrics():
    """Benchmark data for research paper comparison."""
    return {
        "success": True,
        "summary_metrics": {
            "edusum": {"rouge1": 0.524, "rouge2": 0.281, "rougeL": 0.442, "bertscore": 0.912, "meteor": 0.385},
            "baselines": {
                "bart": {"rouge1": 0.421, "rouge2": 0.194, "rougeL": 0.352},
                "t5": {"rouge1": 0.405, "rouge2": 0.182, "rougeL": 0.338},
                "textrank": {"rouge1": 0.312, "rouge2": 0.115, "rougeL": 0.245},
            },
        },
        "vision_metrics": {
            "saeocr": {"wer": 0.082, "cer": 0.031, "accuracy": 91.8},
            "tesseract": {"wer": 0.425, "cer": 0.184, "accuracy": 57.5},
        },
        "educational_utility": {
            "concept_extraction": 4.8,
            "summarization_quality": 4.6,
            "exam_relevance": 4.5,
            "flashcard_utility": 4.7,
            "graph_coherence": 4.4,
        },
    }


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
