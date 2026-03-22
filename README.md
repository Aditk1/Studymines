# Studymines 📚

**Studymines** is an AI-powered educational platform that transforms raw study materials—from PDFs and slide decks to photographs of handwritten notes—into structured, student-ready study packages. 

Using advanced Vision LLMs , Studymines extracts semantic meaning from any format and generates adaptive summaries, flashcards, and exam questions tailored to your educational level.

---

## ✨ Key Features

- **Multimodal Extraction**: Process PDFs, PPTX, DOCX, and images (handwritten notes, whiteboards) with ease.
- **Vision-Augmented OCR**: Custom SAEOCR (Semantically Aware Educational OCR) for high-accuracy handwriting recognition.
- **Leveled Learning**: Adaptive output generation for High School, Undergraduate, and Postgraduate students.
- **Study Packages**: Automatically generates:
  - 📝 **Adaptive Summaries**
  - 🧠 **Key Concept Extractions**
  - 🗂️ **Interactive Flashcards**
  - 🎓 **Bloom's Taxonomy-Aligned Quiz Questions**
- **Ecosystem Rankings**: Gamified learning leaderboard to track growth and retention.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (SQLite/PostgreSQL)
- **Frontend**: React, Tailwind CSS, Framer Motion, Vite
- **AI Core**: Google Gemini 1.5 Pro (Vision + Text)
- **Parsing**: PyMuPDF, python-pptx, python-docx, OpenCV

---

## 🚀 Quick Start

### 1. Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # venv\Scripts\activate on Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root:
   ```env
   DATABASE_URL=sqlite:///./studymines.db
   GOOGLE_API_KEY=your_gemini_api_key
   ```
4. Start the server:
   ```bash
   python app/main.py
   ```

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install & Start:
   ```bash
   npm install
   npm run dev
   ```

---

## 📂 Project Structure

```text
studymines/
├── app/                # FastAPI backend logic
├── frontend/           # React frontend (Vite)
├── tests/              # Backend unit tests
├── .env                # Core configuration
└── requirements.txt    # Python dependencies
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
