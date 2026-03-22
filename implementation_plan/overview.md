# 🧠 Cognitive Learning System Implementation Plan

This implementation plan outlines the integration of **Studymines** (Adaptive Learning Platform) and **RLM-GraphRAG** (Advanced Knowledge Graph RAG) into a unified, next-generation AI-powered educational ecosystem: **eduRAG**.

## 🏗️ Core Integration Architecture

The system will transition from simple vector-based search to a hybrid architecture combining the hierarchical structure of Studymines with the entity-relationship mapping of RLM-GraphRAG.

### Key Components

| Component | Functionality | Project Origin |
| :--- | :--- | :--- |
| **Ingestion Bridge** | Cross-extracts facts and entities from documents to build the Knowledge Graph. | RLM-GraphRAG |
| **Study Lab Engine** | Generates adaptive study packages (notes, summaries, questions). | Studymines |
| **Graph-Aware Tutor** | AI tutor that uses graph traversal for cross-document reasoning. | RLM + Studymines |
| **Cognitive Dashboard** | Tracks confidence levels and knowledge progression across entities. | Studymines |

---

## 📅 Roadmap: Phase 1 (Core Integration)

### 1. Unified Ingestion Pipeline
- **Goal**: Ensure every PDF uploaded to Studymines is processed through RLM-GraphRAG to build a local Knowledge Graph.
- **Workflow**:
    1. Document upload via Studymines FastAPI.
    2. RLM-GraphRAG Entity Extraction (`src/ingestion`).
    3. Community detection for topic clustering.
    4. Storage in a unified Graph/Vector DB.

### 2. Graph-Enhanced Study Packages
- **Goal**: Enrich study packages with "Related Key Concepts" and "Background Facts" from the Knowledge Graph.
- **Integration**:
    - Modify `study_package.py` to query the Knowledge Graph for entities mentioned in the current chapter.
    - Provide "Contextual Links" between related study materials.

---

## 🛠️ Working Integrations

### 🔌 Ingestion Bridge (RLM ↔ Studymines)
Located at `app/bridge_service.py`, this service will call the GraphRAG pipeline whenever a new file is added to a Studymines project.
- **Trigger**: File upload event.
- **Output**: Populated Graph database + Vector embeddings.

### 🧠 Cognitive Reasoning Engine
A new module to handle complex user queries that require connecting dots between multiple files.
- **Technology**: Multi-hop graph traversal.
- **Use Case**: "Compare the concept of photosynthesis from *Biology 101* with the energy conversion in *Intro to Physics*."

---

## 🚀 Advanced Functionalities

- **Confidence-Aware Re-Tutoring**: The tutor identifies "weak spots" (represented as entities with low user-interaction scores) and proactively suggests remedial study packages.
- **Global Knowledge Map**: A visual 3D graph of all entities in the user's workspace, showing connections and mastery levels.
- **Automatic Question Generation**: Using the Knowledge Graph to generate harder "application-level" questions (Bloom's Taxonomy).

---

> [!IMPORTANT]
> This folder contains detailed breakdowns for each module. Refer to `knowledge_graph_ingestion.md` and `cognitive_tutoring.md` for technical specifications.
