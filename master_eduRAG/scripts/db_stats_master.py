
import sqlite3
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, "master_edurag.db")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables in master_edurag.db: {tables}")
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"Table {table}: {count} rows")
            except Exception as e:
                print(f"Could not query table {table}: {e}")
            
    except Exception as e:
        print(f"Error querying database: {e}")
else:
    print(f"Database file not found at {db_path}")
