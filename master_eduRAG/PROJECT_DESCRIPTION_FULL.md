# Project Description

## 1. Project Title

**eduRAG (master_eduRAG) - Cognitive Learning System**

---

## 2. One-Line Description of What It Does

eduRAG is an AI-powered educational platform that reads uploaded study materials, converts them into summaries, concepts, flashcards, and questions, and answers user queries using Knowledge Graph based reasoning.

---

## 3. Problem Statement

Students and teachers often work with educational resources that are scattered across many formats such as PDFs, PowerPoint presentations, Word documents, plain text files, scanned notes, and images. These resources are difficult to revise quickly because they are not automatically organized into structured learning material. Traditional systems may store files, but they generally do not understand the academic content deeply, connect related concepts, or provide intelligent support for revision and question answering.

eduRAG solves this problem by automatically extracting content from documents and images, processing the text, generating study resources, and building a Knowledge Graph from the uploaded material. This allows the system to provide both study support and graph-grounded academic answers.

---

## 4. Target Users

The project is mainly designed for:

- **Students** who want summaries, flashcards, concept explanations, and AI-based help while studying
- **Teachers** who want to organize content, support students, and manage academic workflows
- **Classrooms and academic groups** that need structured learning support
- **Educational institutions** that want an AI-assisted learning platform

---

## 5. Problem It Solves

The project addresses the gap between raw educational material and meaningful learning support. In normal study workflows, users often spend large amounts of time:

- reading long documents
- creating short notes manually
- identifying important concepts
- designing revision questions
- connecting topics across chapters
- understanding scanned or image-based notes

eduRAG reduces this effort by turning uploaded learning resources into structured educational outputs. It also improves academic question answering by using concept relationships through a Knowledge Graph, rather than relying only on plain text retrieval.

---

## 6. Who It Is For

This project is intended for:

- school and college students
- undergraduate and postgraduate learners
- teachers and instructors
- departments and institutions interested in smart education tools

It is especially useful for users who study from mixed-format materials such as notes, PDFs, slides, handwritten content, and scanned resources.

---

## 7. How It Works

The working of the system can be explained in the following stages:

### 7.1 File Upload

The user uploads a document or image such as a PDF, PPTX, DOCX, TXT file, or note image.

### 7.2 Text Extraction

The system extracts text using:

- document parsers for digital files
- OCR for scanned images and handwritten/printed note images

### 7.3 Preprocessing

The extracted text is cleaned and prepared for educational processing.

### 7.4 Chunking and Analysis

Large content is divided into smaller chunks so that the AI pipeline can process it effectively.

### 7.5 Study Package Generation

The system generates useful learning outputs such as:

- summary
- important concepts
- flashcards
- practice questions

### 7.6 Knowledge Graph Construction

The system extracts entities and relationships from the content and stores them as a Knowledge Graph.

### 7.7 Graph-Based Question Answering

When the user asks a question, the system retrieves graph-related and vector-based context, then produces a grounded answer.

### 7.8 LMS and Analytics Support

The platform also supports classrooms, assignments, assessments, reminders, analytics, and academic risk tracking.

---

## 8. List of All Modules / Features

The project contains the following major modules and features:

### 8.1 User Authentication Module

Supports signup, login, role-based access, and profile management for students, teachers, and admins.

### 8.2 Document Upload Module

Allows users to upload educational files such as PDF, DOCX, PPTX, and TXT for processing.

### 8.3 Image Upload and OCR Module

Accepts image-based material and extracts text from scanned or note images.

### 8.4 Text Preprocessing Module

Cleans and normalizes extracted text to improve downstream output quality.

### 8.5 Content Segregation Module

Helps organize content by subject and topic for better learning relevance.

### 8.6 Chunking Module

Splits large documents into smaller parts for easier analysis and generation.

### 8.7 Study Package Generation Module

Produces:

- summary
- concepts
- flashcards
- practice questions

### 8.8 Knowledge Graph Module

Builds a graph of educational concepts and relationships from the uploaded material.

### 8.9 Graph Query Module

Answers user questions through graph traversal and retrieval-based reasoning.

### 8.10 Chatbot / Cognitive Consultant

Provides AI-based support for asking questions related to uploaded study material.

### 8.11 Dashboard Module

Displays study artifacts, learning progress, and user information.

### 8.12 Leaderboard Module

Shows comparative learning or platform activity data.

### 8.13 Classroom / LMS Module

Supports courses, sections, modules, enrollments, and classroom workflows.

### 8.14 Assignment and Assessment Module

Handles question banks, assessments, attempts, and feedback.

### 8.15 Analytics Module

Tracks performance and educational activity.

### 8.16 Academic Risk Module

Identifies students at risk based on engagement and mastery-related signals.

### 8.17 Scheduler and Reminder Module

Supports study reminders and task scheduling.

### 8.18 Research and Benchmarking Module

Supports experiments, OCR benchmarking, and GraphRAG evaluation workflows.

---

## 9. Technology Used

The project combines web development, AI, OCR, graph processing, and vector retrieval technologies.

### 9.1 Languages

- Python
- JavaScript

### 9.2 Backend Frameworks and Tools

- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- python-dotenv

### 9.3 Frontend Frameworks and Tools

- React
- Vite
- Tailwind CSS
- Framer Motion
- Axios
- React Router

### 9.4 AI / NLP / ML Libraries

- Transformers
- Sentence-Transformers
- spaCy
- PyTorch

### 9.5 OCR and Document Processing Tools

- PyMuPDF
- python-docx
- python-pptx
- PaddleOCR
- OpenCV
- Pillow
- Marker
- Docling

### 9.6 Knowledge Graph and Graph Libraries

- NetworkX
- CDlib
- Leidenalg
- igraph

### 9.7 Vector and Retrieval Support

- ChromaDB

### 9.8 LLM / AI Providers

- Ollama
- Groq
- Gemini
- Cerebras
- OpenRouter
- OpenAI-compatible integrations
- Anthropic-compatible integrations

### 9.9 Database

- SQL-based database through SQLAlchemy models
- Local project database used during development

---

## 10. Input -> Process -> Output Flow

### Input

The user gives:

- a PDF, DOCX, PPTX, or TXT file
- an image or scanned note
- or a natural language question

### Process

The system performs the following workflow:

1. file upload or question submission
2. document parsing or OCR-based extraction
3. preprocessing and text cleaning
4. chunking of content
5. study package generation
6. concept and relationship extraction
7. Knowledge Graph construction
8. vector storage and retrieval support
9. graph-based question answering
10. presentation of outputs on the frontend

### Output

The system returns:

- summary
- concept list
- flashcards
- practice questions
- graph-grounded answers
- analytics and learning insights

---

## 11. System Architecture

The system follows a layered architecture where the frontend communicates with the backend, and the backend controls the document-processing, AI, graph, and database layers.

### 11.1 Frontend Layer

The frontend is built with React and provides the interface for:

- authentication
- upload
- dashboard
- chatbot
- classrooms
- analytics
- study lab
- assignments
- profile and other academic views

### 11.2 Backend API Layer

The backend is built with FastAPI and acts as the main controller of the application. It handles:

- user authentication
- document and image uploads
- study package generation
- graph query endpoints
- LMS operations
- analytics and reminders

### 11.3 Parsing and OCR Layer

This layer handles the extraction of text from:

- digital documents
- scanned educational content
- image-based notes

### 11.4 Preprocessing and Chunking Layer

This layer cleans and splits text to prepare it for AI generation and graph building.

### 11.5 Study Package Generation Layer

This layer generates educational outputs such as summaries, concepts, flashcards, and questions.

### 11.6 RAG Bridge Layer

This layer connects the study package generation side with the graph reasoning side.

### 11.7 GraphRAG Engine

This layer:

- extracts triples
- scores them for confidence
- builds a Knowledge Graph
- detects graph communities
- performs traversal and retrieval
- generates grounded answers

### 11.8 Vector Store Layer

This layer stores embeddings for semantic retrieval and relevance matching.

### 11.9 Database Layer

This layer stores:

- users
- uploads
- study artifacts
- graph entities
- performance data
- classrooms
- assessments
- reminders
- analytics logs

### 11.10 Architecture Flow

```text
User
  |
  v
React Frontend
  |
  v
FastAPI Backend
  |
  +--> Authentication / LMS / Analytics
  |
  +--> Document Parsing / OCR
          |
          v
     Preprocessing + Chunking
          |
          v
     Study Package Generation
          |
          v
        RAG Bridge
          |
          +--> Knowledge Graph Engine
          +--> ChromaDB Vector Store
          +--> SQL Database
          |
          v
     Final Answer / Study Outputs
          |
          v
      Frontend Display
```

---

## 12. SDG Relevance

This project directly relates to:

**SDG 4 - Quality Education**

The platform supports quality education by making learning materials easier to understand, revise, and interact with. It helps students study more effectively and supports teachers with content generation, academic management, and analytics.

---

## 13. Group Member Names

**Group Name:** Group One

**Group Members:**

- [Add Member 1 Name]
- [Add Member 2 Name]
- [Add Member 3 Name]
- [Add Member 4 Name]

---

## 14. Guide Name

**Dr. Sarika Zaware**

---

## 15. College Name and Department

**College Name:** [Add College Name Here]  
**Department:** Department of Computer Science

---

## 16. Academic Year and Semester

**Academic Year:** [Add Academic Year Here]  
**Semester:** [Add Semester Here]

---

## 17. Summary

eduRAG is a full-stack educational AI platform that combines document understanding, OCR, study material generation, Knowledge Graph construction, graph-based question answering, LMS functionality, and analytics. It is designed to help students learn more effectively and help teachers manage academic content and student support more intelligently. The project stands out because it transforms raw educational material into structured, interactive, and explainable learning support.
