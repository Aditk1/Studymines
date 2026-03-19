"""
Main FastAPI application for EduSum.
Handles file/image uploads, processing, and study package generation.
"""

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import tempfile
import json
from typing import Optional

from app.database import init_db, get_db
from app.models import User, Upload, Performance
from app.parsers.document_parser import parse_document
from app.vision.image_preprocessor import ImagePreprocessor
from app.vision.vision_extractor import extract_from_image
from app.preprocessing import preprocess_text
from app.segregation import segregate_content
from app.llm.epf_generator import generate_study_package
from app.chunking import chunk_and_process
from app.config import MAX_FILE_SIZE, MAX_IMAGE_SIZE, ALLOWED_DOCUMENT_TYPES, ALLOWED_IMAGE_TYPES

# Initialize FastAPI app
app = FastAPI(
    title="EduSum - Educational Summarization System",
    description="AI-powered educational content summarization with vision support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Could not connect to database: {e}")
        print("  Set up PostgreSQL and update DATABASE_URL in .env")
        print("  Non-database features (parsing, text preprocessing) will still work")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "EduSum",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload_document": "/api/v1/upload/document",
            "upload_image": "/api/v1/upload/image",
            "user_dashboard": "/api/v1/users/{user_id}",
            "leaderboard": "/api/v1/leaderboard",
            "create_user": "/api/v1/users",
            "get_or_create_user": "/api/v1/users/guest/{username}"
        }
    }


@app.post("/api/v1/users")
async def create_user(
    name: str = Form(...),
    email: str = Form(...),
    student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db)
):
    """Create a new user."""
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return {
                "id": existing.id,
                "name": existing.name,
                "email": existing.email,
                "student_level": existing.student_level,
                "message": "User already exists"
            }
        
        # Create new user
        user = User(name=name, email=email, student_level=student_level)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "student_level": user.student_level,
            "message": "User created successfully"
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.post("/api/v1/auth/signup")
async def signup(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return JSONResponse(status_code=400, content={"error": "Email already registered"})
        
        user = User(
            name=name,
            email=email,
            password_hash=password, # In a real app, use hashing here
            student_level=student_level
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "student_level": user.student_level
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/v1/auth/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Login an existing user."""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or user.password_hash != password:
            return JSONResponse(status_code=401, content={"error": "Invalid email or password"})
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "student_level": user.student_level
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/v1/users/guest/{username}")
async def get_or_create_guest_user(username: str, db: Session = Depends(get_db)):
    """Get or create a guest user by username."""
    try:
        # Try to find user by email (username@guest.local)
        email = f"{username}@guest.local"
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new guest user
            user = User(
                name=username,
                email=email,
                student_level="undergraduate"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "student_level": user.student_level
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.post("/api/v1/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document (PDF, PPTX, DOCX).
    
    Args:
        file: Document file.
        user_id: ID or username of the user uploading.
        subject: Optional subject name (for manual segregation).
        topic: Optional topic name (for manual segregation).
        student_level: Student level for output adaptation.
        db: Database session.
        
    Returns:
        Study package with all outputs.
    """
    try:
        # Get or create user
        if user_id.isdigit():
            user = db.query(User).filter(User.id == int(user_id)).first()
        else:
            # Use guest user endpoint logic
            email = f"{user_id}@guest.local"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(name=user_id, email=email, student_level=student_level)
                db.add(user)
                db.commit()
                db.refresh(user)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Save temp file and validate size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Validate file extension
        file_ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_ext not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}"
            )

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Parse document
            parsed = parse_document(tmp_path)
            text = parsed["text"]

            # Preprocess text
            text = preprocess_text(text)

            # Segregate content
            segregation = segregate_content(text, subject, topic, file.filename)

            # Generate study package (uses chunking + map-reduce for long documents)
            study_package = chunk_and_process(
                text,
                student_level,
                segregation.get("subject"),
                segregation.get("topic")
            )

            # Save upload record
            upload_record = Upload(
                user_id=user.id,
                file_name=file.filename,
                file_type=parsed["metadata"].get("file_type", "unknown"),
                subject=segregation.get("subject"),
                topic=segregation.get("topic"),
                study_package=json.dumps(study_package)
            )
            db.add(upload_record)
            db.commit()

            return {
                "success": True,
                "upload_id": upload_record.id,
                "file_name": file.filename,
                "segregation": segregation,
                "study_package": study_package if study_package.get("success") else {"error": study_package.get("error")}
            }
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/v1/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    student_level: str = Form("undergraduate"),
    db: Session = Depends(get_db)
):
    """
    Upload and process an image (photo of notes, scanned paper, etc.).
    
    Args:
        file: Image file.
        user_id: ID or username of the user uploading.
        subject: Optional subject name.
        topic: Optional topic name.
        student_level: Student level for output adaptation.
        db: Database session.
        
    Returns:
        Study package with extracted content.
    """
    try:
        # Get or create user
        if user_id.isdigit():
            user = db.query(User).filter(User.id == int(user_id)).first()
        else:
            # Use guest user endpoint logic
            email = f"{user_id}@guest.local"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(name=user_id, email=email, student_level=student_level)
                db.add(user)
                db.commit()
                db.refresh(user)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Save temp file and validate size
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Image too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)}MB"
            )

        # Validate image type
        file_ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_ext not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type: {file_ext}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Preprocess image
            preprocessed_image = ImagePreprocessor.preprocess(tmp_path)

            # Extract from image using Gemini Vision (SAEOCR)
            extraction = extract_from_image(tmp_path)

            # Check extraction quality — PRD: "fall back to legibility warning"
            if not extraction.get("extracted_text"):
                raise ValueError("Failed to extract text from image. The image may be too blurry or low quality.")

            if extraction.get("confidence") == "low":
                legibility_warning = (
                    "Warning: Low confidence extraction. "
                    f"Issues: {extraction.get('issues', 'Image quality may be poor')}. "
                    "Results may be incomplete or inaccurate."
                )
            else:
                legibility_warning = None

            # Preprocess extracted text
            text = preprocess_text(extraction["extracted_text"])

            # Segregate content
            segregation = segregate_content(text, subject, topic, file.filename)

            # Generate study package (uses chunking for long extracted text)
            study_package = chunk_and_process(
                text,
                student_level,
                segregation.get("subject"),
                segregation.get("topic")
            )

            # Save upload record
            upload_record = Upload(
                user_id=user.id,
                file_name=file.filename,
                file_type="image",
                subject=segregation.get("subject"),
                topic=segregation.get("topic"),
                study_package=json.dumps(study_package)
            )
            db.add(upload_record)
            db.commit()

            response = {
                "success": True,
                "upload_id": upload_record.id,
                "file_name": file.filename,
                "extraction_confidence": extraction.get("confidence"),
                "content_type": extraction.get("content_type"),
                "segregation": segregation,
                "study_package": study_package if study_package.get("success") else {"error": study_package.get("error")}
            }
            if legibility_warning:
                response["legibility_warning"] = legibility_warning
            return response
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/v1/users/{user_id}")
async def get_user_dashboard(user_id: str, db: Session = Depends(get_db)):
    """Get user dashboard with uploads and performance history."""
    try:
        # Get user by ID or username
        if user_id.isdigit():
            user = db.query(User).filter(User.id == int(user_id)).first()
        else:
            email = f"{user_id}@guest.local"
            user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Try to create guest user
            email = f"{user_id}@guest.local"
            user = User(name=user_id, email=email, student_level="undergraduate")
            db.add(user)
            db.commit()
            db.refresh(user)

        uploads = db.query(Upload).filter(Upload.user_id == user.id).all()
        performance = db.query(Performance).filter(Performance.user_id == user.id).all()

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "student_level": user.student_level
            },
            "uploads": [
                {
                    "id": u.id,
                    "file_name": u.file_name,
                    "subject": u.subject,
                    "topic": u.topic,
                    "created_at": u.uploaded_at.isoformat()
                }
                for u in uploads
            ],
            "uploads_count": len(uploads),
            "performance": {
                "avg_score": sum(p.score for p in performance) / len(performance) if performance else 0,
                "total_scores": len(performance)
            },
            "rank": 0  # Will be calculated from leaderboard
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.get("/api/v1/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    """Get leaderboard with top performing users."""
    try:
        # Query all users with their upload counts and average scores
        from sqlalchemy import func
        
        results = db.query(
            User.id,
            User.name,
            User.email,
            func.count(Upload.id).label("uploads_count"),
            func.coalesce(func.avg(Performance.score), 0).label("avg_score")
        ).outerjoin(Upload, User.id == Upload.user_id
        ).outerjoin(Performance, User.id == Performance.user_id
        ).group_by(User.id, User.name, User.email
        ).order_by(func.coalesce(func.avg(Performance.score), 0).desc(), 
                   func.count(Upload.id).desc()
        ).all()

        leaderboard = [
            {
                "rank": i + 1,
                "user_id": r.id,
                "name": r.name,
                "email": r.email,
                "uploads_count": int(r.uploads_count) if r.uploads_count else 0,
                "score": float(r.avg_score) if r.avg_score else 0
            }
            for i, r in enumerate(results)
        ]

        return leaderboard
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.get("/api/v1/uploads/{upload_id}")
async def get_upload_status(upload_id: int, db: Session = Depends(get_db)):
    """Retrieve an existing upload and its study package."""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Parse back the study package JSON
    package_data = {}
    if upload.study_package:
        try:
            package_data = json.loads(upload.study_package)
        except:
            package_data = {"error": "Could not parse study package"}

    return {
        "success": True,
        "id": upload.id,
        "file_name": upload.file_name,
        "subject": upload.subject,
        "topic": upload.topic,
        "study_package": package_data
    }


@app.get("/api/v1/research/metrics")
async def get_research_metrics(db: Session = Depends(get_db)):
    """Retrieve benchmarking metrics for the research paper."""
    # In a real scenario, we would read from app/evaluation/results/
    # For the UI preview, we provide the benchmark data from the PRD
    return {
        "success": True,
        "summary_metrics": {
            "edusum": {
                "rouge1": 0.524,
                "rouge2": 0.281,
                "rougeL": 0.442,
                "bertscore": 0.912,
                "meteor": 0.385
            },
            "baselines": {
                "bart": {"rouge1": 0.421, "rouge2": 0.194, "rougeL": 0.352},
                "t5": {"rouge1": 0.405, "rouge2": 0.182, "rougeL": 0.338},
                "textrank": {"rouge1": 0.312, "rouge2": 0.115, "rougeL": 0.245}
            }
        },
        "vision_metrics": {
            "saeocr": {"wer": 0.082, "cer": 0.031, "accuracy": 91.8},
            "tesseract": {"wer": 0.425, "cer": 0.184, "accuracy": 57.5}
        },
        "educational_utility": {
            "leveled_adaptation": 4.8,
            "concept_retention": 4.5,
            "structural_clarity": 4.7,
            "quiz_relevance": 4.6
        }
    }


@app.post("/api/v1/performance")
async def record_performance(
    upload_id: int = Form(...),
    user_id: str = Form(...),
    score: float = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Record quiz performance or user rating."""
    # Verify upload exists
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Get user
    if user_id.isdigit():
        user = db.query(User).filter(User.id == int(user_id)).first()
    else:
        email = f"{user_id}@guest.local"
        user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    perf = Performance(
        user_id=user.id,
        upload_id=upload_id,
        score=score,
        notes=notes
    )
    db.add(perf)
    db.commit()
    db.refresh(perf)
    
    return {"success": True, "performance_id": perf.id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
