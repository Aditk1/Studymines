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

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import os, tempfile, json, uuid, shutil
import cv2
from typing import Optional

from app.database import init_db, get_db
from app.models import User, Upload, Performance, GraphEntity, EventLog, Usage
from app.parsers.document_parser import parse_document
from app.vision.image_preprocessor import ImagePreprocessor
from app.vision.vision_extractor import extract_from_image
from app.preprocessing import preprocess_text
from app.segregation import segregate_content
from app.chunking import chunk_and_process
from app.config import MAX_FILE_SIZE, MAX_IMAGE_SIZE, ALLOWED_DOCUMENT_TYPES, ALLOWED_IMAGE_TYPES
from app.research_metrics import get_research_metrics
from src.utils.error_handler import explain_error

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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Catch-all exception handler that reports errors beautifully to the CLI
    while yielding a standard JSON 500 Response.
    """
    explain_error(exc, context=f"Request to: {request.url}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "cause": "An unexpected error occurred. See server logs for details."}
    )


@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        print("✓ Database initialised successfully")
    except Exception as e:
        print(f"WARNING: DB init warning: {e}")

# Include LMS WebSocket router
from app.lms.chat_socket import router as lms_ws_router
app.include_router(lms_ws_router, prefix="/api/v1")

# Include LMS Analytics router 
from app.lms.api.analytics import router as lms_analytics_router
app.include_router(lms_analytics_router, prefix="/api/v1")

# Include Core LMS CRUD router
from app.lms.api.lms_routes import router as lms_routes_router
app.include_router(lms_routes_router, prefix="/api/v1")


IMAGE_UPLOAD_TYPES = set(ALLOWED_IMAGE_TYPES) | {"image"}
PROCESSING_GRAPH_STATUS = "processing_graph"
GRAPH_GROUNDED_STATUS = "graph_grounded"


def _stage_one_artifact(stage_one_package: dict) -> dict:
    artifact = dict(stage_one_package or {})
    artifact["status"] = PROCESSING_GRAPH_STATUS
    return artifact


def _derive_upload_processing_status(upload: Upload) -> str:
    if upload.graph_path or upload.graph_triples_count:
        return GRAPH_GROUNDED_STATUS
    if not upload.study_package:
        return "archived"

    try:
        payload = json.loads(upload.study_package)
    except Exception:
        return PROCESSING_GRAPH_STATUS

    return payload.get("status", PROCESSING_GRAPH_STATUS)


def _parse_study_package_payload(raw_payload: Optional[str]) -> dict:
    if not raw_payload:
        return {}

    try:
        payload = json.loads(raw_payload)
    except Exception:
        return {}

    if isinstance(payload, dict) and "package" in payload and isinstance(payload.get("package"), dict):
        payload = payload["package"]

    if isinstance(payload, dict) and "data" not in payload:
        if any(key in payload for key in ["summary", "concepts", "flashcards", "questions"]):
            payload = {
                "success": bool(payload.get("success", True)),
                "data": {
                    "summary": payload.get("summary", {}),
                    "concepts": payload.get("concepts", []),
                    "flashcards": payload.get("flashcards", []),
                    "questions": payload.get("questions", []),
                },
                "graph_metadata": payload.get("graph_metadata", {}),
                "status": payload.get("status", PROCESSING_GRAPH_STATUS),
            }

    return payload if isinstance(payload, dict) else {}


def _build_stage_one_context(upload: Upload, package: dict) -> str:
    data = package.get("data", {}) if isinstance(package, dict) else {}
    summary = data.get("summary", {}) or {}
    concepts = data.get("concepts", []) or []
    flashcards = data.get("flashcards", []) or []
    questions = data.get("questions", []) or []

    concept_lines = [
        f"- {concept.get('name', 'Concept')}: {concept.get('definition', '')}"
        for concept in concepts[:8]
    ]
    flashcard_lines = [
        f"- Q: {card.get('question', '')} | A: {card.get('answer', '')}"
        for card in flashcards[:5]
    ]
    question_lines = [
        f"- {item.get('question', '')}"
        for item in questions[:5]
    ]

    return "\n".join([
        f"Artifact: {upload.file_name}",
        f"Subject: {upload.subject or 'Unknown'}",
        f"Topic: {upload.topic or upload.file_name}",
        f"Summary Title: {summary.get('title', '')}",
        f"Summary: {summary.get('content', '')}",
        "Concepts:",
        "\n".join(concept_lines) or "- None",
        "Flashcards:",
        "\n".join(flashcard_lines) or "- None",
        "Questions:",
        "\n".join(question_lines) or "- None",
    ])


def _answer_from_study_package(question: str, upload: Upload) -> Optional[dict]:
    package = _parse_study_package_payload(upload.study_package)
    if not package.get("data"):
        return None

    context = _build_stage_one_context(upload, package)
    graph_status = _derive_upload_processing_status(upload)

    prompt = f"""You are a study assistant answering a student's question from a Stage 1 study package.

Use only the provided package context. If the answer is not clearly supported by the package, say that the deep graph is still processing and answer cautiously from the available notes.
Keep the response concise and helpful.

PACKAGE CONTEXT:
{context}

QUESTION:
{question}
"""

    try:
        from app.llm.epf_generator import EPFGenerator

        answer = EPFGenerator()._generate_content(prompt).strip()
    except Exception:
        summary = package.get("data", {}).get("summary", {}) or {}
        answer = summary.get("content") or "The deep graph is still processing, and I do not have enough grounded context yet."

    return {
        "success": True,
        "answer": answer,
        "nodes_visited": 0,
        "traversal_depth": 0,
        "strategy": "stage_one_fallback",
        "latency_seconds": 0.0,
        "graph_status": graph_status,
        "is_graph_ready": bool(upload.graph_path or upload.graph_triples_count),
    }


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

from app.lms.auth import create_access_token, detect_role_from_email, get_current_user, get_password_hash, verify_password

@app.post("/api/v1/auth/signup")
async def signup(
    name: str = Form(...), email: str = Form(...),
    password: str = Form(...), student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    
    Args:
        name: User's full name
        email: Unique email address
        password: User password (stored as plaintext - consider hashing)
        student_level: Academic level (elementary, high_school, undergraduate, postgraduate)
        role: User role (student, teacher, admin)
        
    Returns:
        Success response with access token and user details, or 400 if email already registered
    """
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return JSONResponse(status_code=400, content={"error": "Email already registered"})
    
    # Use auto-detected role instead of client-supplied role for security
    role = detect_role_from_email(email)
    hashed_password = get_password_hash(password)
    user = User(name=name, email=email, password_hash=hashed_password, student_level=student_level, role=role)
    db.add(user); db.commit(); db.refresh(user)
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "success": True, 
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "student_level": user.student_level}
    }


@app.post("/api/v1/auth/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Authenticate user and issue access token.
    
    Args:
        email: User email address
        password: User password
        
    Returns:
        Success response with access token and user details, or 401 if invalid credentials
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return JSONResponse(status_code=401, content={"error": "Invalid email or password"})
    
    # Auto-detect role on login as requested
    detected_role = detect_role_from_email(email)
    if user.role != detected_role:
        user.role = detected_role
        db.commit(); db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "success": True, 
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "student_level": user.student_level}
    }


@app.post("/api/v1/users")
async def create_user(name: str = Form(...), email: str = Form(...), student_level: str = Form("undergraduate"), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return {"id": existing.id, "name": existing.name, "email": existing.email, "role": existing.role, "student_level": existing.student_level, "message": "User already exists"}
    
    role = detect_role_from_email(email)
    user = User(name=name, email=email, student_level=student_level, role=role)
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "student_level": user.student_level, "message": "User created"}


@app.get("/api/v1/users/guest/{username}")
async def get_or_create_guest(username: str, db: Session = Depends(get_db)):
    email = f"{username}@guest.local"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        role = detect_role_from_email(email)
        user = User(name=username, email=email, student_level="undergraduate", role=role)
        db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "student_level": user.student_level}


# ════════════════════════════════════════────────────────────────────────────────
# Document Upload  (Studymines + RAG Bridge)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    student_level: str = Form("undergraduate"),
    analyze: bool = Form(True),
    user_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Process document uploads (PDF, DOCX, etc.)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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

    if not analyze:
        upload_rec = Upload(
            user_id=user.id, file_name=file.filename,
            file_type=file_ext,
            subject=subject or 'GeneralArchive', topic=topic or 'Untitled Document',
            file_path=permanent_path,
            study_package=None
        )
        db.add(upload_rec)
        db.commit()
        db.refresh(upload_rec)
        return {"success": True, "upload_id": upload_rec.id, "file_name": file.filename, "message": "File arched. Pending analysis.", "is_analyzed": False}

    from app.orchestrator import StudyMinesPipeline
    from app.chunking import chunk_and_generate_eps, enrich_study_package_with_rag
    try:
        pipeline = StudyMinesPipeline()
        parsed = pipeline.process_document(permanent_path)
        
        text = preprocess_text(parsed.get("text", ""))
        segregation = segregate_content(text, subject, topic, file.filename)

        # --- STAGE 1: Fast Multi-Provider Generation ---
        stage_one_package = await chunk_and_generate_eps(
            text, student_level,
            segregation.get("subject"), segregation.get("topic"),
        )
        artifact = _stage_one_artifact(stage_one_package)

        # Persist initial package
        upload_rec = Upload(
            user_id=user.id, file_name=file.filename,
            file_type=parsed.get("metadata", {}).get("type", "unknown"),
            subject=segregation.get("subject"), topic=segregation.get("topic"),
            file_path=permanent_path,
            study_package=json.dumps(artifact),
        )
        db.add(upload_rec)
        db.commit()
        db.refresh(upload_rec)

        # --- STAGE 2: Background Llama RAG Enrichment ---
        if background_tasks is not None:
            background_tasks.add_task(
                enrich_study_package_with_rag,
                upload_rec.id, text, file.filename, artifact
            )
        else:
            await enrich_study_package_with_rag(upload_rec.id, text, file.filename, artifact)

        return {
            "success": True, 
            "upload_id": upload_rec.id, 
            "file_name": file.filename,
            "study_package": artifact,
            "status": PROCESSING_GRAPH_STATUS,
            "message": "Harvest complete! Exploring deep connections (RAG) in the background. You will be notified when the graph is ready."
        }
    except Exception as e:
        print(f"DEBUG_UPLOAD_DOC ERROR: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


# ═══════════════════════════════════════════════════════════════
# Image Upload  (Studymines Vision + RAG Bridge)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    student_level: str = Form("undergraduate"),
    analyze: bool = Form(True),
    user_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload and process an image (JPG, PNG, etc.).
    
    The image is preprocessed using computer vision, text is extracted via OCR,
    and the extracted content is processed through the study package and graph generation pipeline.
    
    Args:
        file: Image file to upload
        user_id: ID of user uploading the image
        subject: Optional subject classification
        topic: Optional topic classification
        student_level: Academic level for content generation (default: undergraduate)
        
    Returns:
        Upload record with extracted text, study_package, and graph metadata
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=413, detail="Image too large")

        file_ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if file_ext not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported image type: {file_ext}")

        # Generate permanent storage path - Force .jpg for better compatibility
        save_dir = "data/uploads"
        os.makedirs(save_dir, exist_ok=True)
        unique_filename = f"{uuid.uuid4()}.jpg"
        permanent_path = os.path.join(save_dir, unique_filename)

        with open(permanent_path, "wb") as f:
            f.write(content)

        if not analyze:
            upload_rec = Upload(
                user_id=user.id, file_name=file.filename,
                file_type=file_ext,
                subject=subject or 'GeneralArchive', topic=topic or 'Untitled Document',
                file_path=permanent_path,
                study_package=None
            )
            db.add(upload_rec)
            db.commit()
            db.refresh(upload_rec)
            return {"success": True, "upload_id": upload_rec.id, "file_name": file.filename, "message": "File arched. Pending analysis.", "is_analyzed": False}

        from app.chunking import chunk_and_generate_eps, enrich_study_package_with_rag
        try:
            preprocessed = ImagePreprocessor.preprocess(permanent_path)
            cv2.imwrite(permanent_path, preprocessed)
            
            extraction = extract_from_image(permanent_path)
            text = extraction.get("extracted_text", "")
            if not text:
                raise HTTPException(status_code=400, detail="No text could be extracted from image")

            segregation = segregate_content(text, subject, topic, file.filename)

            # --- STAGE 1: Fast Gemini Generation ---
            stage_one_package = await chunk_and_generate_eps(
                text, student_level,
                segregation.get("subject"), segregation.get("topic"),
            )
            artifact = _stage_one_artifact(stage_one_package)

            # Persist initial package
            upload_rec = Upload(
                user_id=user.id, file_name=file.filename, file_type=file_ext,
                subject=segregation.get("subject"), topic=segregation.get("topic"),
                file_path=permanent_path,
                study_package=json.dumps(artifact),
            )
            db.add(upload_rec)
            db.commit()
            db.refresh(upload_rec)

            # --- STAGE 2: Background Llama RAG Enrichment ---
            if background_tasks is not None:
                background_tasks.add_task(
                    enrich_study_package_with_rag,
                    upload_rec.id, text, file.filename, artifact
                )
            else:
                await enrich_study_package_with_rag(upload_rec.id, text, file.filename, artifact)

            print(f"DEBUG_UPLOAD_IMAGE: success record_id={upload_rec.id}")

            legibility_warning = extraction.get("issues")
            resp = {
                "success": True,
                "upload_id": upload_rec.id,
                "file_name": file.filename,
                "extraction_confidence": extraction.get("confidence"),
                "segregation": segregation,
                "study_package": artifact,
                "status": PROCESSING_GRAPH_STATUS,
                "message": "Harvest complete! Deep connection synthesis is running in the background."
            }
            if legibility_warning:
                resp["warning"] = legibility_warning

            return resp

        except Exception as inner_e:
            import traceback
            traceback.print_exc()
            print(f"DEBUG_UPLOAD_IMAGE inner Exception: {inner_e}")
            raise HTTPException(status_code=500, detail=str(inner_e))

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG_UPLOAD_IMAGE major Exception: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/upload/{upload_id}/analyze")
async def analyze_artifact(upload_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Triggers the detailed AI analysis and GraphRAG compilation for an Archived item."""
    upload_rec = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).first()
    if not upload_rec:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if upload_rec.study_package:
        return {"success": True, "message": "Already compiled"}

    user = db.query(User).filter(User.id == upload_rec.user_id).first()
    
    permanent_path = upload_rec.file_path
    file_name = upload_rec.file_name
    student_level = user.student_level if user else "undergraduate"
    
    try:
        if upload_rec.file_type and upload_rec.file_type.lower() in IMAGE_UPLOAD_TYPES:
            preprocessed = ImagePreprocessor.preprocess(permanent_path)
            cv2.imwrite(permanent_path, preprocessed)
            extraction = extract_from_image(permanent_path)
            if not extraction.get("extracted_text"):
                raise ValueError("Failed to extract text from image.")
            text = preprocess_text(extraction["extracted_text"])
        else:
            parsed = parse_document(permanent_path)
            text = preprocess_text(parsed["text"])

        segregation = segregate_content(text, upload_rec.subject, upload_rec.topic, file_name)
        raw_res = await chunk_and_process(
            text, student_level,
            segregation.get("subject"), segregation.get("topic"),
            source_name=file_name,
        )
        study_package = raw_res["package"]
        graph_stats = raw_res["stats"]

        graph_meta = study_package.get("graph_metadata", {})
        upload_rec.study_package = json.dumps(study_package)
        upload_rec.graph_path = graph_meta.get("graph_path") or graph_stats.get("graph_path")
        upload_rec.graph_triples_count = graph_meta.get("triples_count") or graph_stats.get("num_triples")
        upload_rec.graph_confidence = graph_meta.get("extraction_confidence") or graph_stats.get("extraction_confidence")
        db.commit()

        from app.models import GraphEntity
        for node_name in graph_stats.get("nodes", []):
            entity = GraphEntity(
                upload_id=upload_rec.id,
                entity_name=str(node_name),
                entity_type="vision_concept" if upload_rec.file_type in ["jpg", "png"] else "concept",
            )
            db.add(entity)
        db.commit()
        return {"success": True, "upload_id": upload_rec.id, "message": "Analysis compiled."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/upload/{upload_id}")
async def delete_artifact(upload_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Delete an artifact from StudyMines."""
    upload_rec = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).first()
    if not upload_rec:
        raise HTTPException(status_code=404, detail="Artifact not found")
    db.delete(upload_rec)
    db.commit()
    return {"success": True}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════
# Graph Endpoints  (NEW — RLM-GraphRAG)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/v1/uploads/all")
async def get_all_uploads(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Fetch all document uploads for the current user."""
    uploads = db.query(Upload).filter(Upload.user_id == user.id).all()
    return [
        {
            "id": u.id, 
            "file_name": u.file_name, 
            "subject": u.subject, 
            "topic": u.topic,
            "created_at": u.uploaded_at.isoformat(),
            "is_analyzed": bool(u.study_package),
            "processing_status": _derive_upload_processing_status(u),
            "is_graph_ready": bool(u.graph_path or u.graph_triples_count),
        }
        for u in uploads
    ]

@app.post("/api/v1/graph/query")
async def graph_query(
    question: str = Form(...),
    upload_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Multi-hop question answering over the Knowledge Graph.
    
    Performs semantic reasoning using the RLM-GraphRAG engine to answer questions
    by traversing the knowledge graph constructed from uploaded documents. Uses:
    - Seed entity linking (C1)
    - Graph traversal with RLM-REPL (C3)
    - Multi-entity parallel dispatch (C4)
    - Context assembly and answer generation
    
    Args:
        question: Natural language question to answer
        upload_id: Optional upload ID to constrain query to specific document's graph
        
    Returns:
        Answer with supporting context, confidence scores, and traversal metadata
    """
    from app.bridge import RAGBridge

    graph_path = None
    upload = None
    if upload_id:
        upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).first()
        if upload:
            graph_path = upload.graph_path
        else:
            raise HTTPException(status_code=403, detail="Not authorized for this upload")

    if upload and not graph_path:
        fallback = _answer_from_study_package(question, upload)
        if fallback:
            return fallback
        return {
            "success": False,
            "error": "This artifact is still being prepared. Ask again once graph grounding completes.",
            "graph_status": _derive_upload_processing_status(upload),
            "is_graph_ready": False,
        }

    bridge = RAGBridge()
    result = await bridge.query_graph(question, graph_path)
    if (not result.get("success")) and upload and result.get("error") == "No graph available. Ingest a document first.":
        fallback = _answer_from_study_package(question, upload)
        if fallback:
            return fallback
        result["graph_status"] = _derive_upload_processing_status(upload)
        result["is_graph_ready"] = bool(upload.graph_path or upload.graph_triples_count)
    return result


@app.post("/api/v1/graph/chat")
async def graph_chat(
    message: str = Form(...),
    upload_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Graph-grounded chatbot interface.
    
    Alias for graph_query optimized for conversational interactions. Allows students
    to ask follow-up questions about document content with graph-based reasoning.
    
    Args:
        message: User message / question
        upload_id: Optional upload ID for context
        
    Returns:
        Chatbot response with graph-grounded context
    """
    return await graph_query(question=message, upload_id=upload_id, db=db, user=user)


@app.get("/api/v1/graph/view/{upload_id}")
async def graph_view(upload_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Return graph metadata for a specific upload."""
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    return {
        "upload_id": upload.id,
        "file_name": upload.file_name,
        "graph_path": upload.graph_path,
        "triples_count": upload.graph_triples_count,
        "extraction_confidence": upload.graph_confidence,
        "status": _derive_upload_processing_status(upload),
        "is_graph_ready": bool(upload.graph_path or upload.graph_triples_count),
    }


@app.get("/api/v1/graph/entities")
async def graph_entities(upload_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """List entities extracted for a specific upload."""
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).first()
    if not upload:
        raise HTTPException(status_code=403, detail="Not authorized for this upload")
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

@app.get("/api/v1/users/me")
async def get_user_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # user is already resolved via get_current_user
    uploads = db.query(Upload).filter(Upload.user_id == user.id).all()
    performance = db.query(Performance).filter(Performance.user_id == user.id).all()

    # Calculate study hours from event logs (mocked for now, but linked to log count)
    log_count = db.query(EventLog).filter(EventLog.user_id == user.id).count()
    study_hours = round(log_count * 0.15, 1) # ~9 mins per logged event

    return {
        "user": {
            "id": user.id, "name": user.name, "email": user.email, 
            "student_level": user.student_level, "role": user.role
        },
        "uploads": [
            {"id": u.id, "file_name": u.file_name, "subject": u.subject, "topic": u.topic,
             "graph_path": u.graph_path, "graph_triples_count": u.graph_triples_count, "created_at": u.uploaded_at.isoformat(), 
             "is_analyzed": bool(u.study_package), "processing_status": _derive_upload_processing_status(u),
             "is_graph_ready": bool(u.graph_path or u.graph_triples_count)}
            for u in uploads
        ],
        "uploads_count": len(uploads),
        "performance": {
            "avg_score": sum(p.score for p in performance) / len(performance) if performance else 0,
            "total_scores": len(performance),
            "study_hours": study_hours
        },
    }

@app.get("/api/v1/users/{user_id}")
async def get_user_profile(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch profile data for a specific user ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Optional: logic to restrict viewing other people's profiles if not admin/teacher
    # For now, we allow it for the demo/dev
    
    uploads = db.query(Upload).filter(Upload.user_id == user.id).all()
    performance = db.query(Performance).filter(Performance.user_id == user.id).all()
    log_count = db.query(EventLog).filter(EventLog.user_id == user.id).count()
    study_hours = round(log_count * 0.15, 1)

    return {
        "user": {
            "id": user.id, "name": user.name, "email": user.email, 
            "student_level": user.student_level, "role": user.role
        },
        "uploads": [
            {"id": u.id, "file_name": u.file_name, "subject": u.subject, "topic": u.topic,
             "graph_path": u.graph_path, "graph_triples_count": u.graph_triples_count, "created_at": u.uploaded_at.isoformat(), 
             "is_analyzed": bool(u.study_package), "processing_status": _derive_upload_processing_status(u),
             "is_graph_ready": bool(u.graph_path or u.graph_triples_count)}
            for u in uploads
        ],
        "uploads_count": len(uploads),
        "performance": {
            "avg_score": sum(p.score for p in performance) / len(performance) if performance else 0,
            "total_scores": len(performance),
            "study_hours": study_hours
        },
    }

@app.get("/api/v1/stats/ecosystem")
async def get_ecosystem_stats(db: Session = Depends(get_db)):
    """Global aggregate stats for the sidebar."""
    from app.models import GraphEntity
    
    total_users = db.query(User).count()
    total_uploads = db.query(Upload).count()
    avg_mastery = db.query(func.avg(GraphEntity.mastery_score)).scalar() or 0.8
    
    return {
        "knowledge_retained": round(float(avg_mastery) * 100, 1),
        "total_study_hours": round(db.query(EventLog).count() * 0.12, 1),
        "total_users": total_users,
        "total_artifacts": total_uploads,
        "active_now": 28 # Static for now, or could count last_active_at < 5 mins
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
async def get_upload_file(upload_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).first()
    if not upload or not upload.file_path or not os.path.exists(upload.file_path):
        raise HTTPException(status_code=404, detail="File not found or access denied")
    return FileResponse(upload.file_path, filename=upload.file_name)


@app.get("/api/v1/uploads/{upload_id}")
async def get_upload(upload_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Unified API for fetching both Studymines Uploads and Classroom LMSMaterials."""
    upload = None
    is_lms = False
    
    # Check if ID is integer (Studymines Upload)
    try:
        u_id_int = int(upload_id)
        upload = db.query(Upload).filter(Upload.id == u_id_int, Upload.user_id == user.id).first()
    except ValueError:
        # Check if ID is string (LMSMaterial UUID)
        u_id_str = str(upload_id)
        from app.lms.models.material import LMSMaterial
        upload = db.query(LMSMaterial).filter(LMSMaterial.id == u_id_str).first()
        is_lms = True

    if not upload:
        raise HTTPException(status_code=404, detail="Artifact not found or access denied")

    pkg = {}
    if upload.study_package:
        try:
            pkg = json.loads(upload.study_package)
            
            # ── Structural Check (Compatibility with old/nested LMS storage) ──
            # if we see {"package": {"data": ...}, "stats": ...}, flatten it.
            if isinstance(pkg, dict) and "package" in pkg and "data" in pkg["package"]:
                 # This is an old material storage correctly fixing it on the fly
                 pkg = pkg["package"]

            # Normalize legacy flat package format to the modern shape expected by frontend.
            # Legacy records may store summary/concepts/flashcards/questions at top-level.
            if isinstance(pkg, dict) and "data" not in pkg:
                if any(k in pkg for k in ["summary", "concepts", "flashcards", "questions"]):
                    normalized_data = {
                        "summary": pkg.get("summary", {}),
                        "concepts": pkg.get("concepts", []),
                        "flashcards": pkg.get("flashcards", []),
                        "questions": pkg.get("questions", []),
                    }
                    pkg = {
                        "success": bool(pkg.get("success", True)),
                        "data": normalized_data,
                        "graph_metadata": pkg.get("graph_metadata", {}),
                    }
        except Exception:
            pkg = {"error": "Could not parse study package"}

    # Consistent renaming for frontend
    title = upload.title if is_lms else upload.file_name
    subject = (upload.classroom.subject if is_lms and upload.classroom else "General") if is_lms else upload.subject
    topic = upload.title if is_lms else upload.topic

    return {
        "success": True, 
        "id": upload.id, 
        "file_name": title,
        "subject": subject, 
        "topic": topic, 
        "study_package": pkg,
        "type": "lms" if is_lms else "upload",
        "processing_status": pkg.get("status", _derive_upload_processing_status(upload)) if isinstance(pkg, dict) else _derive_upload_processing_status(upload),
        "is_graph_ready": bool(getattr(upload, "graph_path", None) or getattr(upload, "graph_triples_count", None)),
    }


@app.post("/api/v1/performance")
async def record_performance(
    upload_id: int = Form(...),
    score: float = Form(...), notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found or access denied")
    perf = Performance(user_id=user.id, upload_id=upload_id, score=score, notes=notes)
    db.add(perf); db.commit(); db.refresh(perf)
    
    # --- LMS BRIDGE: Update Mastery for all linked graph entities ---
    from app.lms.risk_engine import update_mastery_from_quiz, RiskEngine
    entities = db.query(GraphEntity).filter(GraphEntity.upload_id == upload_id).all()
    for ent in entities:
        # Update specific mastery log
        from app.models import MasteryLog
        new_log = MasteryLog(
            user_id=user.id,
            entity_id=ent.id,
            score=score / 100.0 if score > 1.0 else score,
            source_type="assessment"
        )
        db.add(new_log)
        
        # Also update the entity's global mastery score (rolling weight)
        new_mastery = (ent.mastery_score * 0.4) + ( (score/100.0) * 0.6 )
        ent.mastery_score = round(new_mastery, 2)
    db.commit()

    # --- Analytics & Risk Detection: Recalculate if part of a course or classroom ---
    # Trigger global risk engine evaluation for the user (Course 0 as unlisted)
    engine = RiskEngine(db)
    await engine.analyze_student(user.id, 0)

    return {"success": True, "performance_id": perf.id}



@app.get("/api/v1/research/metrics")
async def research_metrics():
    """Research metrics sourced from live artifacts or exported evaluation files."""
    return get_research_metrics()


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
