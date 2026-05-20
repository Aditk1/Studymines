"""
Desktop launcher for master_eduRAG.
Handles environment setup, starts the FastAPI server, and opens the frontend in the default web browser.
"""
import os
import sys
import time
import shutil
import webbrowser
import threading
import uvicorn
from dotenv import load_dotenv

if not os.path.exists(".env") and os.path.exists(".env.example"):
    try:
        shutil.copy(".env.example", ".env")
        print("[OK] Created default .env file from .env.example")
    except Exception as e:
        print(f"WARNING: Could not create .env file: {e}")

# Load configuration variables
load_dotenv(override=True)

# Set default SUPABASE_JWT_SECRET if not set to prevent auth crashes
if not os.getenv("SUPABASE_JWT_SECRET"):
    os.environ["SUPABASE_JWT_SECRET"] = "dev-secret-change-me"
    print("[OK] Configured fallback SUPABASE_JWT_SECRET for authentication")

from app.main import app

def open_browser():
    """Waits for uvicorn to startup and opens browser"""
    time.sleep(2.0)
    url = "http://127.0.0.1:8000"
    print(f"\n====================================================")
    print(f"   Launching default browser at {url}...")
    print(f"====================================================\n")
    webbrowser.open(url)

if __name__ == "__main__":
    print("====================================================")
    print("           master_eduRAG Desktop App Launcher")
    print("====================================================")
    
    # Start web browser daemon thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run uvicorn server
    # We bind to 127.0.0.1 directly as localhost for safety on desktop
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
