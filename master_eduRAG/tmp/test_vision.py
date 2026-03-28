
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append('d:/projects/eduRAG/master_eduRAG')

load_dotenv('d:/projects/eduRAG/master_eduRAG/.env')

from app.vision.vision_extractor import extract_from_image
from app.config import VISION_MODEL, GEMINI_API_KEY

print(f"Model: {VISION_MODEL}")
print(f"API Key exists: {bool(GEMINI_API_KEY)}")

# Test with a dummy image if exists, or just try to initialize
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(VISION_MODEL)
    print("✓ Model initialization successful")
except Exception as e:
    print(f"✗ Model initialization failed: {e}")
