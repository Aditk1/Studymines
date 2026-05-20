"""
Inspect database connectivity and core table availability.
"""

import os
import sys

sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import User, Upload, GraphEntity
from app.lms.models import LMSMaterial, DocumentChunk

def check_db():
    print("=== Database State Verification ===")
    
    with SessionLocal() as db:
        # 1. Check Users
        try:
            users = db.query(User).all()
            print(f"\n[Users]: {len(users)} found")
            for u in users:
                print(f"  - User: {u.id} | Email: {u.email} | Role: {u.role}")
        except Exception as e:
            print(f"Error querying Users: {e}")
            
        # 2. Check Uploads
        try:
            uploads = db.query(Upload).all()
            print(f"\n[Uploads]: {len(uploads)} found")
            for up in uploads:
                status = "graph_ready" if getattr(up, "graph_path", None) or getattr(up, "graph_triples_count", None) else "pending"
                print(f"  - Upload: {up.id} | File: {up.file_name} | Status: {status}")
        except Exception as e:
            print(f"Error querying Uploads: {e}")
            
        # 3. Check LMS Materials
        try:
            materials = db.query(LMSMaterial).all()
            print(f"\n[LMS Materials]: {len(materials)} found")
            for m in materials:
                print(f"  - Material: {m.id} | Title: {m.title} | Status: {m.status} | Study Package: {m.study_package}")
        except Exception as e:
            print(f"Error querying LMS Materials: {e}")
            
        # 4. Check Document Chunks
        try:
            chunks = db.query(DocumentChunk).limit(5).all()
            total_chunks = db.query(DocumentChunk).count()
            print(f"\n[Document Chunks]: {total_chunks} total found")
            for c in chunks:
                print(f"  - Chunk: {c.chunk_id[:8]}... | Material ID: {c.material_id}")
        except Exception as e:
            print(f"Error querying Document Chunks: {e}")
            
        # 5. Check Graph Entities
        try:
            entities = db.query(GraphEntity).limit(5).all()
            total_entities = db.query(GraphEntity).count()
            print(f"\n[Graph Entities (RAG)]: {total_entities} total found")
            for e in entities:
                print(f"  - Entity: {e.entity_name} | Type: {e.entity_type}")
        except Exception as e:
            print(f"Error querying Graph Entities: {e}")

if __name__ == '__main__':
    check_db()
