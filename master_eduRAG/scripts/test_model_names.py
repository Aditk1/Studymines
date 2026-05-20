"""
Developer smoke script for validating configured model names.
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
    exit(1)

genai.configure(api_key=api_key)

models_to_try = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-flash-latest"
]

for m_name in models_to_try:
    print(f"\nTrying model: {m_name}")
    try:
        model = genai.GenerativeModel(m_name)
        response = model.generate_content("Say 'Hello'")
        print(f"✅ Success! Response: {response.text.strip()}")
        break
    except Exception as e:
        print(f"❌ Failed: {e}")
