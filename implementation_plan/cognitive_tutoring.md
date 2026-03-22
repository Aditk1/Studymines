# 🤖 Cognitive Tutoring & AI Reasoning

The AI Tutor in **eduRAG** will go beyond simple RAG by performing multi-hop reasoning over the Knowledge Graph.

## 🧠 Reasoning Capabilities

### 1. Cross-Document Synthesis
- **Scenario**: User asks about a topic covered in three different PDFs.
- **Action**: The tutor traverses the graph to find common entities shared between files and synthesizes a holistic answer.

### 2. Conceptual Gap Detection
- **Mechanism**: Compare the user's "Knowledge Map" (entities they have verified/mastered) against the "Domain Graph" (all entities in the document).
- **Output**: "I noticed you're asking about Quantum Tunneling, but we haven't covered Wave-Particle Duality yet. Would you like a quick refresher?"

## 💬 Tutoring Interface

- **Confidence Scores**: The tutor tracks how confident it is in its own answers based on graph path length and node centrality.
- **Reference Citations**: Every answer provides a clickable link to the entity in the graph view and the source chunk in the PDF.

## 🛠️ Technical Integration

- **LLM Prompting**: Move from basic system prompts to "Reasoning Chains" that explicitly query the graph for related entities before generating responses.
- **State Management**: Use Redis or a temporary memory store to keep track of the conversation "Current Concept Focal Point".
