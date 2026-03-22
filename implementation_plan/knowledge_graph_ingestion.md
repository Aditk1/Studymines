# 📊 Knowledge Graph Ingestion Strategy

This document details the workflow for processing educational content into a structured Knowledge Graph.

## 🛠️ Ingestion Workflow

1.  **Document Preprocessing**:
    -   Split PDFs using `chunking.py` from Studymines.
    -   Extract high-quality text and metadata (page numbers, headers).

2.  **Entity & Relationship Extraction**:
    -   Utilize RLM-GraphRAG's extraction agents.
    -   Identify `Concepts`, `Definitions`, `Theorems`, `Examples`, and `Historical Figures`.
    -   Map relationships like `isa`, `depends_on`, `contradicts`, `correlates_with`.

3.  **Community Clustering**:
    -   Run Leica or Louvain community detection to group related entities into "Modules".
    -   Automatically label these communities as "Study Chapters".

## 💾 Storage Layer

-   **Graph DB**: Neo4j or NetworkX (local) for entity-relationship storage.
-   **Vector DB**: FAISS or ChromaDB for semantic retrieval of raw context.
-   **Structured DB**: SQLite (edusum.db) for user metadata, scores, and study package tracking.

## 🚀 Implementation Steps

- [ ] Create `GraphBridge` class in `eduRAG/app/core/bridge.py`.
- [ ] Connect Studymines `FileService` to GraphRAG `Pipeline`.
- [ ] Implement incremental updates (don't rebuild the graph for every new file).
