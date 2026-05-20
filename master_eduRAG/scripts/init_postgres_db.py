"""
Initialize PostgreSQL tables for the SQLAlchemy schema.
"""

import os
import sys

# Ensure the root of the project is in the path
sys.path.append(os.getcwd())

from app.database import init_db

def main():
    print("Initializing Database Tables...")
    try:
        init_db()
        print("Successfully created all database tables.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    main()
