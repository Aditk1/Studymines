# 🗄️ Database & Schema Integration

To merge Studymines and RLM-GraphRAG, we need a unified data layer that handles relational user data, unstructured chunks, and structured graph entities.

## 🛠️ Unified Database Architecture

1.  **User State (Relational)**:
    -   Table `users`: IDs, authentication.
    -   Table `workspaces`: Projects, file listings.
    -   Table `confidence_scores`: Entity-level mastery tracking.

2.  **Context Store (Vector)**:
    -   Table `chunks`: Text content, embeddings, file pointers.
    -   Table `metadata`: Source citations, page numbers.

3.  **Knowledge Map (Graph)**:
    -   Nodes: `Entities`, `Communities`.
    -   Edges: `RelatedTo`, `PrerequisiteOf`, `ExampleOf`.

## 🔄 Migration Plan

1.  Export existing Studymines SQlite database.
2.  Iterate through `processed_files` and run the GraphRAG extraction pipeline.
3.  Inject the extracted entities into the new unified Graph-Relational store.
4.  Update the ORM models in `app/models.py` to support graph query methods.

## 🔒 Consistency Strategy

- Ensure that deleting a file in a workspace triggers a "Cascade Deletion" of its associated chunks and entities in both the vector and graph DBs.
