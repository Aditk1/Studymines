
import os
import sys
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL
from app.utils import get_logger

logger = get_logger("migration")

def migrate():
    """
    Production-grade migration script.
    Checks for missing columns and adds them independently.
    Works for both SQLite & Postgres.
    """
    logger.info(f"Starting migration on {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    columns = [
        ('study_package', 'TEXT'),
        ('graph_path', 'VARCHAR(512)'),
        ('graph_triples_count', 'INTEGER'),
        ('graph_confidence', 'FLOAT'),
        ('file_path', 'VARCHAR(512)')
    ]

    for col_name, col_type in columns:
        # Use a fresh connection for each operation to avoid transaction abort lock-in
        try:
            with engine.connect() as conn:
                # Wrap each in its own transaction block
                with conn.begin():
                    conn.execute(text(f"ALTER TABLE lms_materials ADD COLUMN {col_name} {col_type}"))
                logger.info(f"✅ Added {col_name} to lms_materials")
        except Exception as e:
            err_str = str(e).lower()
            if any(msg in err_str for msg in ["duplicate column", "already exists", "already exist"]):
                logger.info(f"ℹ️ {col_name} already exists. Skipping.")
            else:
                logger.warning(f"❌ Error adding {col_name}: {e}")

    logger.info("Migration complete.")

if __name__ == '__main__':
    migrate()
