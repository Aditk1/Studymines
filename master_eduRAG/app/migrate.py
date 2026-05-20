"""
Database migration helper for evolving the local master_eduRAG schema.
"""

from sqlalchemy import text
import sys
import os

# Ensure the root of the project is in the path
sys.path.append(os.getcwd())

from app.database import engine

def migrate():
    """Manual schema migration for Assessments and Course/Classroom links."""
    print("Initiating Assessment Engine Migration...")
    
    # 1. Check existing columns
    from sqlalchemy import inspect
    ins = inspect(engine)
    existing_cols = [c['name'] for c in ins.get_columns('lms_assessments')]
    
    needed_cols = [
        ('course_id', 'INTEGER'),
        ('classroom_id', 'VARCHAR(36)'),
        ('description', 'TEXT'),
        ('total_points', 'INTEGER DEFAULT 100'),
        ('is_published', 'BOOLEAN DEFAULT FALSE'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in needed_cols:
            if col_name not in existing_cols:
                print(f"Adding column: {col_name}...")
                try:
                    conn.execute(text(f"ALTER TABLE lms_assessments ADD COLUMN {col_name} {col_type}"))
                except Exception as e:
                    print(f"Skipped {col_name}: {e}")
        
        # 2. Handle LMS Materials link if missing
        existing_mat_cols = [c['name'] for c in ins.get_columns('lms_materials')]
        if 'study_package' not in existing_mat_cols:
            print("Adding study_package to Materials...")
            try:
                conn.execute(text("ALTER TABLE lms_materials ADD COLUMN study_package TEXT"))
            except Exception as e:
                print(e)
                
        conn.commit()
    print("✓ Migration complete.")

if __name__ == "__main__":
    migrate()
