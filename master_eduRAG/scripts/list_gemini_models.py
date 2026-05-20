"""
List available Gemini models for the configured Google API key.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

from pathlib import Path
project_root = Path(__file__).parent.parent
load_dotenv(dotenv_path=project_root / ".env")
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ No GOOGLE_API_KEY found in .env")
else:
    try:
        genai.configure(api_key=api_key)
        print("🔍 Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name} (v1beta supported: {'v1beta' in m.__repr__() or 'v1beta' in str(m)})")
    except Exception as e:
        print(f"❌ Error listing models: {e}")
