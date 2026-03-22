# 🧠 master_eduRAG — Cognitive Learning System

> **Studymines × RLM-GraphRAG** — A unified, AI-powered educational platform that combines adaptive study-package generation with confidence-weighted knowledge graph reasoning.

---

## 🏗️ Architecture

```
master_eduRAG/
├── app/                          ← Unified FastAPI Backend
│   ├── main.py                   ← Entry point (all endpoints)
│   ├── config.py                 ← Merged configuration
│   ├── database.py               ← SQLAlchemy setup
│   ├── models.py                 ← User, Upload, Performance, GraphEntity
│   ├── bridge.py                 ← 🔌 RAG Bridge (Studymines ↔ GraphRAG)
│   ├── chunking.py               ← Document chunking + map-reduce
│   ├── preprocessing.py          ← Text cleaning & normalisation
│   ├── segregation.py            ← Subject/topic classification
│   ├── parsers/                  ← PDF, PPTX, DOCX, TXT parsers
│   ├── vision/                   ← Gemini Vision OCR (SAEOCR)
│   └── llm/                      ← EPF generator + retry utilities
├── rag_engine/                   ← RLM-GraphRAG Core (ported from src/)
│   ├── pipeline.py               ← Full ingest + query pipeline
│   ├── ingestion/                ← Triple extraction, confidence scoring
│   ├── graph/                    ← KnowledgeGraph (NetworkX)
│   ├── community/                ← Leiden / CW-Leiden detection
│   ├── traversal/                ← Fixed-hop & RLM REPL traversers
│   ├── retrieval/                ← Seed linking, context assembly
│   └── utils/                    ← LLM client, embeddings, logger
├── config/                       ← YAML configs (base.yaml, variants)
├── data/                         ← Runtime storage
│   ├── graphs/                   ← Persisted .pkl graph files
│   ├── chroma_db/                ← ChromaDB vector store
│   └── uploads/                  ← Temp upload storage
├── requirements.txt              ← Merged dependencies
├── .env.example                  ← Environment template
└── README.md                     ← This file
```

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd master_eduRAG
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. LLM Setup (Ollama + Llama 3)
Ensure Ollama is running (check your system tray or run `ollama serve`). Then pull the model used by the chatbot:
```bash
ollama pull llama3.2:3b
```

### 4. Configure
```bash
# In master_eduRAG folder:
copy .env.example .env
# Edit .env with your GOOGLE_API_KEY (for Vision/SAEOCR features)
```

### 5. Run
**Backend:**
```bash
uvicorn app.main:app --reload --port 8000
```
**Frontend:**
```bash
npm run dev   # in the frontend directory
```

### 6. Interactive Interface
- **App**: `http://localhost:5173`
- **API Docs**: `http://localhost:8000/docs`

---

## 🤖 Cognitive Consultant (Chatbot)

The system now includes a global **Cognitive Consultant** chatbot (accessible via the floating brain icon) that:
1.  **Context-Aware**: Automatically links to the document you are currently studying.
2.  **Graph-Grounded**: Uses the RLM-GraphRAG C3/C4 traversal to find multi-hop answers.
3.  **Local inference**: Powered by Llama 3 via Ollama for privacy and high performance.

---

---

## 🔌 Core Integration: The RAG Bridge

The `app/bridge.py` module is the heart of the integration:

1. **Ingest**: When a document is uploaded, the bridge sends extracted text to the RLM-GraphRAG pipeline for triple extraction, confidence scoring, and graph construction.
2. **Enrich**: Study packages (flashcards, concepts, questions) are enriched with graph metadata and confidence labels.
3. **Query**: Students can ask multi-hop questions that traverse the Knowledge Graph for cross-document reasoning.

---

## 📡 API Endpoints

### Studymines (Adaptive Learning)
| Method | Endpoint | Purpose |
|:---|:---|:---|
| `POST` | `/api/v1/upload/document` | Upload PDF/PPTX/DOCX → study package |
| `POST` | `/api/v1/upload/image` | Upload image → OCR → study package |
| `POST` | `/api/v1/auth/signup` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login |
| `GET` | `/api/v1/users/{id}` | User dashboard |
| `GET` | `/api/v1/leaderboard` | Top performers |
| `POST` | `/api/v1/performance` | Record quiz score |

### RLM-GraphRAG (Knowledge Graph)
| Method | Endpoint | Purpose |
|:---|:---|:---|
| `POST` | `/api/v1/graph/query` | Multi-hop QA over Knowledge Graph |
| `POST` | `/api/v1/graph/chat` | Chatbot specific endpoint (alias for query) |
| `GET` | `/api/v1/graph/view/{upload_id}` | Graph metadata for an upload |
| `GET` | `/api/v1/graph/entities?upload_id=N` | List extracted entities |

---

## 🧬 Research Contributions (C1–C4)

| ID | Contribution | Description |
|:---|:---|:---|
| **C1** | Confidence-Scored Extraction | LLM-based scoring for triple extraction |
| **C2** | CW-Leiden Community Detection | Confidence-weighted semantic clustering |
| **C3** | RLM REPL-Guided Traversal | Dynamic LLM-driven graph exploration |
| **C4** | Parallel Multi-Seed Dispatcher | Async multi-entity traversal with convergence |

---

## 🛠️ Tech Stack

- **Backend**: FastAPI + SQLAlchemy + Uvicorn
- **Vision**: Gemini Vision API (SAEOCR)
- **Graph**: NetworkX + CDLib + Leiden
- **Vector**: ChromaDB + Sentence-Transformers
- **LLM**: Gemini / Ollama / OpenAI / Anthropic
- **Evaluation**: ROUGE, BERTScore, Token F1

---


