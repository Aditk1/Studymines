# Function Inventory

## app/__init__.py
- No functions/classes found

## app/bridge.py
- app/bridge.py -> RAGBridge -> Bridges the gap between basic summarisation and graph-based reasoning.
- app/bridge.py -> RAGBridge.__init__ -> Purpose inferred from name/context
- app/bridge.py -> RAGBridge.ingest_to_graph -> Feed extracted text into the RLM-GraphRAG pipeline.
- app/bridge.py -> RAGBridge.enrich_study_package -> Inject graph metadata and confidence labels into a Studymines
- app/bridge.py -> RAGBridge.query_graph -> Multi-hop question answering over the Knowledge Graph.
- app/bridge.py -> process_with_rag -> One-call helper: ingest + enrich. Returns (package, stats)

## app/chunking.py
- app/chunking.py -> DocumentChunker -> Splits long documents into manageable chunks for LLM processing.
- app/chunking.py -> DocumentChunker.__init__ -> Purpose inferred from name/context
- app/chunking.py -> DocumentChunker.estimate_tokens -> Purpose inferred from name/context
- app/chunking.py -> DocumentChunker.needs_chunking -> Purpose inferred from name/context
- app/chunking.py -> DocumentChunker.chunk_text -> Purpose inferred from name/context
- app/chunking.py -> DocumentChunker.needs_map_reduce -> Purpose inferred from name/context
- app/chunking.py -> MapReduceProcessor -> Map-Reduce strategy for long-document study-package generation.
- app/chunking.py -> MapReduceProcessor.__init__ -> Purpose inferred from name/context
- app/chunking.py -> MapReduceProcessor._generate_content -> Purpose inferred from name/context
- app/chunking.py -> MapReduceProcessor.map_chunk -> Purpose inferred from name/context
- app/chunking.py -> MapReduceProcessor.reduce_summaries -> Purpose inferred from name/context
- app/chunking.py -> MapReduceProcessor.process -> Purpose inferred from name/context
- app/chunking.py -> chunk_and_generate_eps -> PHASE 1: Chunk text → generate initial Gemini-powered study package (FAST).
- app/chunking.py -> enrich_study_package_with_rag -> PHASE 2: Ingest into GraphRAG (LLAMA) → Enrich Package → Notify (BACKGROUND).
- app/chunking.py -> chunk_and_process -> Purpose inferred from name/context

## app/clients/__init__.py
- No functions/classes found

## app/clients/gemini_client.py
- app/clients/gemini_client.py -> GeminiClient -> Singleton-like Gemini client manager.
- app/clients/gemini_client.py -> GeminiClient.__init__ -> Initialize Gemini client with API key.
- app/clients/gemini_client.py -> GeminiClient.get_client -> Get or create Gemini client instance.
- app/clients/gemini_client.py -> GeminiClient.get_model -> Get a Gemini model instance.
- app/clients/gemini_client.py -> GeminiClient.get_vision_model -> Get a Gemini Vision model instance.
- app/clients/gemini_client.py -> configure_gemini -> Configure Gemini API with optional API key.
- app/clients/gemini_client.py -> get_model -> Get a Gemini model instance.
- app/clients/gemini_client.py -> get_vision_model -> Get a Gemini Vision model instance.

## app/clients/groq_client.py
- app/clients/groq_client.py -> GroqClient -> Singleton-like Groq client manager.
- app/clients/groq_client.py -> GroqClient.__init__ -> Initialize Groq client with API key.
- app/clients/groq_client.py -> GroqClient._init_client -> Purpose inferred from name/context
- app/clients/groq_client.py -> GroqClient.get_client -> Get or create Groq client singleton instance.
- app/clients/groq_client.py -> GroqClient.generate_text -> Generate a text response using Groq.
- app/clients/groq_client.py -> GroqClient.generate_vision -> Generate a response from an image using Groq Vision (Llama 3.2 Vision).
- app/clients/groq_client.py -> configure_groq -> Configure Groq client with optional API key.
- app/clients/groq_client.py -> get_groq_client -> Get the module-level Groq client, initializing if needed.
- app/clients/groq_client.py -> groq_generate_text -> Convenience function: generate text via Groq.
- app/clients/groq_client.py -> groq_generate_vision -> Convenience function: analyze image via Groq Vision.

## app/clients/ollama_client.py
- app/clients/ollama_client.py -> OllamaClient -> Synchronous client for Ollama API.
- app/clients/ollama_client.py -> OllamaClient.__init__ -> Purpose inferred from name/context
- app/clients/ollama_client.py -> OllamaClient.generate -> Produce a non-streaming response from Ollama.
- app/clients/ollama_client.py -> ollama_generate -> Convenience helper for Ollama generation.

## app/config.py
- No functions/classes found

## app/database.py
- app/database.py -> get_db -> FastAPI dependency for DB session.
- app/database.py -> init_db -> Create all tables.
- app/database.py -> drop_db -> Drop all tables (testing only).

## app/llm/__init__.py
- No functions/classes found

## app/llm/epf_generator.py
- app/llm/epf_generator.py -> EPFGenerator -> Generates educational outputs using the Educational Prompt Framework.
- app/llm/epf_generator.py -> EPFGenerator.__init__ -> Initialize EPF generator with multi-LLM fallback (Gemini -> Groq -> Ollama).
- app/llm/epf_generator.py -> EPFGenerator._call_ollama -> Call local Ollama reasoning pipeline.
- app/llm/epf_generator.py -> EPFGenerator._generate_content -> Centralized generation call (Gemini -> Groq -> Ollama).
- app/llm/epf_generator.py -> EPFGenerator.generate_outputs -> Generate all four educational outputs: summary, concepts, flashcards, questions.
- app/llm/epf_generator.py -> EPFGenerator.generate_summary -> Generate only leveled summary.
- app/llm/epf_generator.py -> EPFGenerator.generate_flashcards -> Generate flashcards for the content.
- app/llm/epf_generator.py -> EPFGenerator.generate_questions -> Generate exam questions covering Bloom's taxonomy.
- app/llm/epf_generator.py -> generate_study_package -> Convenience function to generate complete study package.

## app/llm/utils.py
- app/llm/utils.py -> clean_json_response -> Cleans LLM response text by removing markdown code blocks
- app/llm/utils.py -> retry_with_backoff -> Decorator to retry a function on 429 (Quota Exceeded) or 500 (Internal Error) errors.

## app/lms/api/analytics.py
- app/lms/api/analytics.py -> get_teacher_insight -> Teacher's Insight (Heatmap):
- app/lms/api/analytics.py -> cross_classroom_search -> Cross-Classroom Search:

## app/lms/api/lms_routes.py
- app/lms/api/lms_routes.py -> get_explore_classrooms -> List all available classrooms/cohorts.
- app/lms/api/lms_routes.py -> get_course_architecture_consolidated -> Retrieve full course sections and modules hierarchy with access control.
- app/lms/api/lms_routes.py -> get_chat_history -> Retrieve chat history for a room.
- app/lms/api/lms_routes.py -> ClassroomBase -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> ClassroomCreate -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> ClassroomResponse -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> create_classroom -> Create a new classroom and auto-add the creator.
- app/lms/api/lms_routes.py -> list_classrooms -> List classrooms the user is a member of.
- app/lms/api/lms_routes.py -> JoinRequest -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> join_classroom -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> get_classroom_requests -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> get_global_materials -> Retrieve all ingested materials for the Global Content view.
- app/lms/api/lms_routes.py -> approve_join_request -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> get_classroom -> Get classroom details.
- app/lms/api/lms_routes.py -> upload_material -> Upload material to a classroom, process through RAG, and save.
- app/lms/api/lms_routes.py -> list_materials -> List materials in a classroom.
- app/lms/api/lms_routes.py -> CourseCreate -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> create_new_course -> Create a high-level course in the new AI LMS structure.
- app/lms/api/lms_routes.py -> list_courses_consolidated -> List courses based on user role: Teachers see owned, students see published.
- app/lms/api/lms_routes.py -> SectionCreate -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> create_section -> Architect a new section within a course.
- app/lms/api/lms_routes.py -> ModuleCreate -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> create_module -> Add a learning module to a section.
- app/lms/api/lms_routes.py -> EventCreate -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> log_event -> Log an analytics event (click, view, session tracking).
- app/lms/api/lms_routes.py -> get_mastery_graph_data -> Get summarized mastery data for the interactive graph visualizer.
- app/lms/api/lms_routes.py -> get_risk_report -> Retrieve students at risk for a specific course or across all classrooms.
- app/lms/api/lms_routes.py -> get_reminders -> Retrieve all pending reminders and milestones for the user.
- app/lms/api/lms_routes.py -> ReminderCreate -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> create_reminder -> Manually add a reminder to the chronos.
- app/lms/api/lms_routes.py -> auto_generate_quiz_from_text -> Uses NLP to extract questions from an existing LMSMaterial and populate QuestionBank.
- app/lms/api/lms_routes.py -> UniversalExamCreate -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> background_generate_exam -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> generate_universal_exam -> Universal generation endpoint for Exams and Quizzes using CognitiveAIGenerator.
- app/lms/api/lms_routes.py -> AssessmentSubmission -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> submit_assessment -> Submit a native LMS assessment, calculate score, and update mastery.
- app/lms/api/lms_routes.py -> list_classroom_exams -> List all exams/assessments for a classroom.
- app/lms/api/lms_routes.py -> get_assessment_details -> Retrieve full details for an assessment including all question content.
- app/lms/api/lms_routes.py -> get_all_members -> Fetch all users in the tenant for the management view.
- app/lms/api/lms_routes.py -> update_member_status -> Change user status (active/banned/etc).
- app/lms/api/lms_routes.py -> update_member_role -> Update a user's role (student/teacher/admin).
- app/lms/api/lms_routes.py -> delete_member -> Permanently delete a user (caution).
- app/lms/api/lms_routes.py -> get_all_assignments -> Fetch all assessments assigned across the user's courses.
- app/lms/api/lms_routes.py -> get_cognitive_heatmap -> Aggregate mastery data by concept to show high-struggle areas.
- app/lms/api/lms_routes.py -> get_analytics_kpis -> Core metrics for the analytics dashboard.
- app/lms/api/lms_routes.py -> get_recommended_learning_paths -> Dynamically calculates the recommended next modules/concepts based on KG mastery topology.
- app/lms/api/lms_routes.py -> get_global_chats -> Retrieve all active classroom chat rooms user is part of.
- app/lms/api/lms_routes.py -> create_course -> Create a new course shell.
- app/lms/api/lms_routes.py -> add_course_section -> Add a new section to a course.
- app/lms/api/lms_routes.py -> publish_course_architecture -> Marks a course architecture as published, making it visible to students.
- app/lms/api/lms_routes.py -> AIArchitectRequest -> Purpose inferred from name/context
- app/lms/api/lms_routes.py -> ai_architect_course -> RAG-driven curriculum synthesis.

## app/lms/auth.py
- app/lms/auth.py -> verify_password -> Purpose inferred from name/context
- app/lms/auth.py -> get_password_hash -> Purpose inferred from name/context
- app/lms/auth.py -> detect_role_from_email -> Auto-detect student or teacher based on domain or keywords.
- app/lms/auth.py -> create_access_token -> Purpose inferred from name/context
- app/lms/auth.py -> get_current_user -> Purpose inferred from name/context
- app/lms/auth.py -> get_current_user_optional -> Purpose inferred from name/context
- app/lms/auth.py -> require_role -> Purpose inferred from name/context

## app/lms/chat_socket.py
- app/lms/chat_socket.py -> ConnectionManager -> Purpose inferred from name/context
- app/lms/chat_socket.py -> ConnectionManager.__init__ -> Purpose inferred from name/context
- app/lms/chat_socket.py -> ConnectionManager.connect -> Purpose inferred from name/context
- app/lms/chat_socket.py -> ConnectionManager.disconnect -> Purpose inferred from name/context
- app/lms/chat_socket.py -> ConnectionManager.broadcast -> Purpose inferred from name/context
- app/lms/chat_socket.py -> websocket_endpoint -> WebSocket endpoint for real-time chat.

## app/lms/core/ai_generator.py
- app/lms/core/ai_generator.py -> CognitiveAIGenerator -> Universal AI generator for Quizzes, Exams, and Lesson Plans.

## app/lms/models/__init__.py
- No functions/classes found

## app/lms/models/chat.py
- app/lms/models/chat.py -> ChatRoom -> Purpose inferred from name/context
- app/lms/models/chat.py -> ChatMessage -> Purpose inferred from name/context

## app/lms/models/classroom.py
- app/lms/models/classroom.py -> Classroom -> Purpose inferred from name/context
- app/lms/models/classroom.py -> ClassroomMember -> Purpose inferred from name/context

## app/lms/models/exam.py
- app/lms/models/exam.py -> Exam -> Purpose inferred from name/context
- app/lms/models/exam.py -> ExamClassroom -> Purpose inferred from name/context
- app/lms/models/exam.py -> ExamSubmission -> Purpose inferred from name/context

## app/lms/models/material.py
- app/lms/models/material.py -> LMSMaterial -> Purpose inferred from name/context
- app/lms/models/material.py -> DocumentChunk -> Purpose inferred from name/context

## app/lms/risk_engine.py
- app/lms/risk_engine.py -> RiskEngine -> Analyzes student data to predict academic failure or disengagement.
- app/lms/risk_engine.py -> RiskEngine.__init__ -> Purpose inferred from name/context
- app/lms/risk_engine.py -> RiskEngine.analyze_student -> Calculates a Risk Score (0-100) for a student in a specific course.
- app/lms/risk_engine.py -> RiskEngine._calculate_engagement -> Engagement based on event frequency in the last 7 days.
- app/lms/risk_engine.py -> RiskEngine._calculate_mastery -> Mastery based on historical MasteryLogs.
- app/lms/risk_engine.py -> update_mastery_from_quiz -> Bridge function to record mastery after a quiz attempt.

## app/main.py
- app/main.py -> startup_event -> Purpose inferred from name/context
- app/main.py -> _stage_one_artifact -> Purpose inferred from name/context
- app/main.py -> _derive_upload_processing_status -> Purpose inferred from name/context
- app/main.py -> _parse_study_package_payload -> Purpose inferred from name/context
- app/main.py -> _build_stage_one_context -> Purpose inferred from name/context
- app/main.py -> _answer_from_study_package -> Purpose inferred from name/context
- app/main.py -> root -> Purpose inferred from name/context
- app/main.py -> signup -> Register a new user account.
- app/main.py -> login -> Authenticate user and issue access token.
- app/main.py -> create_user -> Purpose inferred from name/context
- app/main.py -> get_or_create_guest -> Purpose inferred from name/context
- app/main.py -> upload_document -> Process document uploads (PDF, DOCX, etc.).
- app/main.py -> upload_image -> Upload and process an image (JPG, PNG, etc.).
- app/main.py -> analyze_artifact -> Triggers the detailed AI analysis and GraphRAG compilation for an Archived item.
- app/main.py -> delete_artifact -> Delete an artifact from StudyMines.
- app/main.py -> health_check -> Purpose inferred from name/context
- app/main.py -> get_all_uploads -> Fetch all document uploads for the current user.
- app/main.py -> graph_query -> Multi-hop question answering over the Knowledge Graph.
- app/main.py -> graph_chat -> Graph-grounded chatbot interface.
- app/main.py -> graph_view -> Return graph metadata for a specific upload.
- app/main.py -> graph_entities -> List entities extracted for a specific upload.
- app/main.py -> get_user_dashboard -> Purpose inferred from name/context
- app/main.py -> get_user_profile -> Fetch profile data for a specific user ID.
- app/main.py -> get_ecosystem_stats -> Global aggregate stats for the sidebar.
- app/main.py -> get_leaderboard -> Purpose inferred from name/context
- app/main.py -> get_upload_file -> Purpose inferred from name/context
- app/main.py -> get_upload -> Unified API for fetching both Studymines Uploads and Classroom LMSMaterials.
- app/main.py -> record_performance -> Purpose inferred from name/context
- app/main.py -> research_metrics -> Research metrics sourced from live artifacts or exported evaluation files.

## app/migrate.py
- app/migrate.py -> migrate -> Manual schema migration for Assessments and Course/Classroom links.

## app/models.py
- app/models.py -> User -> Mapped to exact Supabase StudyPoint users table.
- app/models.py -> User.__repr__ -> Purpose inferred from name/context
- app/models.py -> Upload -> Document / image upload record.
- app/models.py -> Upload.__repr__ -> Purpose inferred from name/context
- app/models.py -> Performance -> Quiz scores and feedback.
- app/models.py -> Performance.__repr__ -> Purpose inferred from name/context
- app/models.py -> Usage -> Session tracking and API call counts.
- app/models.py -> Usage.__repr__ -> Purpose inferred from name/context
- app/models.py -> GraphEntity -> Tracks Knowledge Graph entities extracted via RLM-GraphRAG.
- app/models.py -> Course -> Top-level container for educational content.
- app/models.py -> Course.__repr__ -> Purpose inferred from name/context
- app/models.py -> Assessment -> LMS Assessment / Exam.
- app/models.py -> Section -> Logical grouping of modules within a course.
- app/models.py -> LessonModule -> Individual learning unit (Video, Document, Quiz).
- app/models.py -> Enrollment -> Student enrollment record with progress tracking.
- app/models.py -> QuestionBank -> Reusable questions linked to Knowledge Graph entities.
- app/models.py -> AssessmentAttempt -> Student performance on an assessment.
- app/models.py -> AcademicRisk -> Tracks students at risk using GraphRAG mastery + engagement data.
- app/models.py -> EventLog -> Raw analytics events for student behavior tracking.
- app/models.py -> MasteryLog -> Historical tracking of concept mastery over time (GraphRAG integration).
- app/models.py -> LMSReminder -> Personalized reminders or scheduled tasks for students/teachers.

## app/parsers/__init__.py
- No functions/classes found

## app/parsers/document_parser.py
- app/parsers/document_parser.py -> DocumentParser -> Abstract base class for document parsers.
- app/parsers/document_parser.py -> DocumentParser.extract_text -> Extract text from document.
- app/parsers/document_parser.py -> DocumentParser.extract_metadata -> Extract metadata (structure, headings, etc.).
- app/parsers/document_parser.py -> PDFParser -> Parser for PDF files using PyMuPDF.
- app/parsers/document_parser.py -> PDFParser.extract_text -> Extract text from PDF while preserving reading order.
- app/parsers/document_parser.py -> PDFParser.extract_metadata -> Extract PDF metadata and structure.
- app/parsers/document_parser.py -> PPTXParser -> Parser for PowerPoint files.
- app/parsers/document_parser.py -> PPTXParser.extract_text -> Extract text from PPTX slides and speaker notes.
- app/parsers/document_parser.py -> PPTXParser.extract_metadata -> Extract PPTX metadata.
- app/parsers/document_parser.py -> DOCXParser -> Parser for Word documents.
- app/parsers/document_parser.py -> DOCXParser.extract_text -> Extract text from DOCX while preserving structure.
- app/parsers/document_parser.py -> DOCXParser.extract_metadata -> Extract DOCX metadata.
- app/parsers/document_parser.py -> TXTParser -> Parser for plain text files.
- app/parsers/document_parser.py -> TXTParser.extract_text -> Extract text from TXT file.
- app/parsers/document_parser.py -> TXTParser.extract_metadata -> Extract TXT metadata.
- app/parsers/document_parser.py -> detect_file_type -> Detect file type using multiple strategies (not just extension).
- app/parsers/document_parser.py -> DocumentParserFactory -> Factory for selecting the right parser based on file type.
- app/parsers/document_parser.py -> DocumentParserFactory.get_parser -> Get appropriate parser for file type.
- app/parsers/document_parser.py -> parse_document -> Convenience function to parse any supported document.

## app/preprocessing.py
- app/preprocessing.py -> TextPreprocessor -> Preprocesses extracted text for quality and consistency.
- app/preprocessing.py -> TextPreprocessor.clean_whitespace -> Purpose inferred from name/context
- app/preprocessing.py -> TextPreprocessor.fix_encoding -> Purpose inferred from name/context
- app/preprocessing.py -> TextPreprocessor.normalize_bullets -> Purpose inferred from name/context
- app/preprocessing.py -> TextPreprocessor.remove_page_artifacts -> Purpose inferred from name/context
- app/preprocessing.py -> TextPreprocessor.normalize_quotes -> Purpose inferred from name/context
- app/preprocessing.py -> TextPreprocessor.preserve_structure -> Purpose inferred from name/context
- app/preprocessing.py -> TextPreprocessor.preprocess -> Purpose inferred from name/context
- app/preprocessing.py -> preprocess_text -> Convenience function.

## app/research_metrics.py
- app/research_metrics.py -> GraphArtifactMetrics -> Purpose inferred from name/context
- app/research_metrics.py -> GraphArtifactMetrics.to_dict -> Purpose inferred from name/context
- app/research_metrics.py -> _round -> Purpose inferred from name/context
- app/research_metrics.py -> _safe_mean -> Purpose inferred from name/context
- app/research_metrics.py -> _load_graph_artifact -> Purpose inferred from name/context
- app/research_metrics.py -> _compute_community_coherence -> Purpose inferred from name/context
- app/research_metrics.py -> _compute_graph_metrics -> Purpose inferred from name/context
- app/research_metrics.py -> _scan_graph_metrics -> Purpose inferred from name/context
- app/research_metrics.py -> _load_db_snapshot -> Purpose inferred from name/context
- app/research_metrics.py -> _load_live_config -> Purpose inferred from name/context
- app/research_metrics.py -> _build_snapshot_metrics -> Purpose inferred from name/context
- app/research_metrics.py -> get_research_metrics -> Purpose inferred from name/context
- app/research_metrics.py -> write_research_snapshot -> Purpose inferred from name/context

## app/segregation.py
- app/segregation.py -> ContentSegregator -> Purpose inferred from name/context
- app/segregation.py -> ContentSegregator.__init__ -> Initialize ContentSegregator with Gemini primary and Groq fallback.
- app/segregation.py -> ContentSegregator.manual_segregate -> Purpose inferred from name/context
- app/segregation.py -> ContentSegregator.auto_segregate -> Purpose inferred from name/context
- app/segregation.py -> ContentSegregator.segregate -> Purpose inferred from name/context
- app/segregation.py -> segregate_content -> Purpose inferred from name/context

## app/utils/__init__.py
- No functions/classes found

## app/utils/config_loader.py
- app/utils/config_loader.py -> get_project_root -> Get the project root directory.
- app/utils/config_loader.py -> get_config_path -> Get the path to a config file.
- app/utils/config_loader.py -> load_config -> Load YAML configuration file.

## app/utils/logger.py
- app/utils/logger.py -> setup_logger -> Set up a structured logger with consistent formatting.
- app/utils/logger.py -> get_logger -> Get or create a logger with the given name.

## app/vision/__init__.py
- No functions/classes found

## app/vision/image_preprocessor.py
- app/vision/image_preprocessor.py -> ImagePreprocessor -> Preprocesses images for vision extraction.
- app/vision/image_preprocessor.py -> ImagePreprocessor.validate_image -> Validate if file is a valid image.
- app/vision/image_preprocessor.py -> ImagePreprocessor.correct_orientation -> Correct image orientation using EXIF metadata.
- app/vision/image_preprocessor.py -> ImagePreprocessor.resize_image -> Resize image to max size while preserving aspect ratio.
- app/vision/image_preprocessor.py -> ImagePreprocessor.enhance_contrast -> Enhance image contrast for better visibility (especially for low-contrast scans).
- app/vision/image_preprocessor.py -> ImagePreprocessor.preprocess -> Apply all preprocessing steps.

## app/vision/vision_extractor.py
- app/vision/vision_extractor.py -> VisionExtractor -> Extracts text and context from images using Gemini Vision API.
- app/vision/vision_extractor.py -> VisionExtractor.__init__ -> Initialize vision extractor with Gemini API.
- app/vision/vision_extractor.py -> VisionExtractor._generate_content -> Centralized vision call (Gemini -> Groq).
- app/vision/vision_extractor.py -> VisionExtractor.extract_from_image -> Extract text and context from image using Gemini Vision with Groq fallback.
- app/vision/vision_extractor.py -> VisionExtractor._read_image_as_base64 -> Read image and encode as base64 for API.
- app/vision/vision_extractor.py -> VisionExtractor.extract_questions -> Extract and segment questions from a question paper image.
- app/vision/vision_extractor.py -> extract_from_image -> Convenience function for vision extraction.

## frontend/postcss.config.js
- No functions/classes found

## frontend/src/App.jsx
- frontend/src/App.jsx -> App -> Purpose inferred from name/context
- frontend/src/App.jsx -> fetchStats -> Purpose inferred from name/context
- frontend/src/App.jsx -> handleLogin -> Purpose inferred from name/context
- frontend/src/App.jsx -> handleLogout -> Purpose inferred from name/context
- frontend/src/App.jsx -> openArtifact -> Purpose inferred from name/context
- frontend/src/App.jsx -> openAssessment -> Purpose inferred from name/context

## frontend/src/components/Analytics.jsx
- frontend/src/components/Analytics.jsx -> Analytics -> Purpose inferred from name/context
- frontend/src/components/Analytics.jsx -> fetchData -> Purpose inferred from name/context

## frontend/src/components/AssessmentView.jsx
- frontend/src/components/AssessmentView.jsx -> AssessmentView -> Purpose inferred from name/context
- frontend/src/components/AssessmentView.jsx -> fetchDetails -> Purpose inferred from name/context
- frontend/src/components/AssessmentView.jsx -> handleAnswer -> Purpose inferred from name/context
- frontend/src/components/AssessmentView.jsx -> handleSubmit -> Purpose inferred from name/context

## frontend/src/components/Assignments.jsx
- frontend/src/components/Assignments.jsx -> Assignments -> Purpose inferred from name/context
- frontend/src/components/Assignments.jsx -> fetchAssignments -> Purpose inferred from name/context
- frontend/src/components/Assignments.jsx -> fetchClassrooms -> Purpose inferred from name/context
- frontend/src/components/Assignments.jsx -> handleGenerateExam -> Purpose inferred from name/context

## frontend/src/components/Auth.jsx
- frontend/src/components/Auth.jsx -> Auth -> Purpose inferred from name/context
- frontend/src/components/Auth.jsx -> handleSubmit -> Purpose inferred from name/context

## frontend/src/components/Chatbot.jsx
- frontend/src/components/Chatbot.jsx -> Chatbot -> Purpose inferred from name/context
- frontend/src/components/Chatbot.jsx -> scrollToBottom -> Purpose inferred from name/context
- frontend/src/components/Chatbot.jsx -> handleSend -> Purpose inferred from name/context

## frontend/src/components/ClassroomDetail.jsx
- frontend/src/components/ClassroomDetail.jsx -> ClassroomDetail -> Purpose inferred from name/context
- frontend/src/components/ClassroomDetail.jsx -> fetchBaseData -> Purpose inferred from name/context
- frontend/src/components/ClassroomDetail.jsx -> fetchExams -> Purpose inferred from name/context
- frontend/src/components/ClassroomDetail.jsx -> fetchRequests -> Purpose inferred from name/context
- frontend/src/components/ClassroomDetail.jsx -> handleGenerateExam -> Purpose inferred from name/context
- frontend/src/components/ClassroomDetail.jsx -> handleApprove -> Purpose inferred from name/context
- frontend/src/components/ClassroomDetail.jsx -> handleFileUpload -> Purpose inferred from name/context
- frontend/src/components/ClassroomDetail.jsx -> sendChatMessage -> Purpose inferred from name/context

## frontend/src/components/Classrooms.jsx
- frontend/src/components/Classrooms.jsx -> Classrooms -> Purpose inferred from name/context
- frontend/src/components/Classrooms.jsx -> ChevronRight -> Purpose inferred from name/context
- frontend/src/components/Classrooms.jsx -> fetchClassrooms -> Purpose inferred from name/context

## frontend/src/components/Content.jsx
- frontend/src/components/Content.jsx -> Content -> Purpose inferred from name/context
- frontend/src/components/Content.jsx -> handleAnalyze -> Purpose inferred from name/context
- frontend/src/components/Content.jsx -> handleDelete -> Purpose inferred from name/context
- frontend/src/components/Content.jsx -> fetchMaterials -> Purpose inferred from name/context

## frontend/src/components/Dashboard.jsx
- frontend/src/components/Dashboard.jsx -> Dashboard -> Purpose inferred from name/context
- frontend/src/components/Dashboard.jsx -> confirmDelete -> Purpose inferred from name/context
- frontend/src/components/Dashboard.jsx -> fetchUserData -> Purpose inferred from name/context

## frontend/src/components/GlobalChat.jsx
- frontend/src/components/GlobalChat.jsx -> GlobalChat -> Purpose inferred from name/context
- frontend/src/components/GlobalChat.jsx -> fetchChats -> Purpose inferred from name/context

## frontend/src/components/GlobalContent.jsx
- frontend/src/components/GlobalContent.jsx -> GlobalContent -> Purpose inferred from name/context
- frontend/src/components/GlobalContent.jsx -> fetchMaterials -> Purpose inferred from name/context

## frontend/src/components/Header.jsx
- frontend/src/components/Header.jsx -> Header -> Purpose inferred from name/context

## frontend/src/components/KnowledgeMap.jsx
- frontend/src/components/KnowledgeMap.jsx -> buildLinks -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> buildEntityGraph -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> buildConceptFallback -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> normalizeText -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> getLinkNodeId -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> truncateText -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> findRelevantSummary -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> buildNodeExplainer -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> KnowledgeMap -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> LearningPathList -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> refreshGraph -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> getMasteryColor -> Purpose inferred from name/context
- frontend/src/components/KnowledgeMap.jsx -> handleNodeClick -> Purpose inferred from name/context

## frontend/src/components/Leaderboard.jsx
- frontend/src/components/Leaderboard.jsx -> Leaderboard -> Purpose inferred from name/context
- frontend/src/components/Leaderboard.jsx -> fetchLeaderboard -> Purpose inferred from name/context

## frontend/src/components/Members.jsx
- frontend/src/components/Members.jsx -> Members -> Purpose inferred from name/context
- frontend/src/components/Members.jsx -> notify -> Purpose inferred from name/context
- frontend/src/components/Members.jsx -> fetchMembers -> Purpose inferred from name/context
- frontend/src/components/Members.jsx -> handleStatusChange -> Purpose inferred from name/context
- frontend/src/components/Members.jsx -> handleRoleChange -> Purpose inferred from name/context
- frontend/src/components/Members.jsx -> handleViewMastery -> Purpose inferred from name/context
- frontend/src/components/Members.jsx -> handleDelete -> Purpose inferred from name/context

## frontend/src/components/Navigation.jsx
- frontend/src/components/Navigation.jsx -> Navigation -> Purpose inferred from name/context

## frontend/src/components/Profile.jsx
- frontend/src/components/Profile.jsx -> Profile -> Purpose inferred from name/context
- frontend/src/components/Profile.jsx -> ChevronRight -> Purpose inferred from name/context
- frontend/src/components/Profile.jsx -> fetchUserStats -> Purpose inferred from name/context

## frontend/src/components/Research.jsx
- frontend/src/components/Research.jsx -> Research -> Purpose inferred from name/context
- frontend/src/components/Research.jsx -> fetchMetrics -> Purpose inferred from name/context
- frontend/src/components/Research.jsx -> formatMetric -> Purpose inferred from name/context
- frontend/src/components/Research.jsx -> MetricCard -> Purpose inferred from name/context

## frontend/src/components/Scheduler.jsx
- frontend/src/components/Scheduler.jsx -> Scheduler -> Purpose inferred from name/context
- frontend/src/components/Scheduler.jsx -> fetchReminders -> Purpose inferred from name/context
- frontend/src/components/Scheduler.jsx -> handleAddEvent -> Purpose inferred from name/context
- frontend/src/components/Scheduler.jsx -> handleMarkComplete -> Purpose inferred from name/context
- frontend/src/components/Scheduler.jsx -> handleOptimizeCycle -> Purpose inferred from name/context

## frontend/src/components/StudyLab.jsx
- frontend/src/components/StudyLab.jsx -> StudyLab -> Purpose inferred from name/context
- frontend/src/components/StudyLab.jsx -> fetchData -> Purpose inferred from name/context
- frontend/src/components/StudyLab.jsx -> handleQuizAnswer -> Purpose inferred from name/context

## frontend/src/components/TeacherStudio.jsx
- frontend/src/components/TeacherStudio.jsx -> TeacherStudio -> Purpose inferred from name/context
- frontend/src/components/TeacherStudio.jsx -> normalizeCourse -> Purpose inferred from name/context
- frontend/src/components/TeacherStudio.jsx -> fetchCourses -> Purpose inferred from name/context
- frontend/src/components/TeacherStudio.jsx -> handleCreateCourse -> Purpose inferred from name/context
- frontend/src/components/TeacherStudio.jsx -> handleAIArchitect -> Purpose inferred from name/context
- frontend/src/components/TeacherStudio.jsx -> handlePublish -> Purpose inferred from name/context
- frontend/src/components/TeacherStudio.jsx -> generateQuiz -> Purpose inferred from name/context

## frontend/src/components/Upload.jsx
- frontend/src/components/Upload.jsx -> Upload -> Purpose inferred from name/context
- frontend/src/components/Upload.jsx -> handleFileChange -> Purpose inferred from name/context
- frontend/src/components/Upload.jsx -> handleSubmit -> Purpose inferred from name/context

## frontend/src/main.jsx
- No functions/classes found

## frontend/src/supabase.js
- No functions/classes found

## frontend/tailwind.config.js
- No functions/classes found

## frontend/vite.config.js
- No functions/classes found

## outputs/browser_audit.js
- No functions/classes found

## scripts/__init__.py
- No functions/classes found

## scripts/db_stats.py
- No functions/classes found

## scripts/db_stats_master.py
- No functions/classes found

## scripts/diagnostics/check_db.py
- scripts/diagnostics/check_db.py -> check_db -> Purpose inferred from name/context

## scripts/diagnostics/diagnostic_suite.py
- scripts/diagnostics/diagnostic_suite.py -> test_imports -> Purpose inferred from name/context
- scripts/diagnostics/diagnostic_suite.py -> test_db_connection -> Purpose inferred from name/context
- scripts/diagnostics/diagnostic_suite.py -> test_pdf_parser -> Purpose inferred from name/context
- scripts/diagnostics/diagnostic_suite.py -> test_llm_generation -> Purpose inferred from name/context
- scripts/diagnostics/diagnostic_suite.py -> test_rag_ingestion_smoke -> Purpose inferred from name/context
- scripts/diagnostics/diagnostic_suite.py -> run_all -> Purpose inferred from name/context

## scripts/diagnostics/prod_stress_check.py
- scripts/diagnostics/prod_stress_check.py -> check_endpoint -> Purpose inferred from name/context
- scripts/diagnostics/prod_stress_check.py -> main -> Purpose inferred from name/context

## scripts/generate_research_plots.py
- scripts/generate_research_plots.py -> plot_full_graph -> Purpose inferred from name/context
- scripts/generate_research_plots.py -> plot_communities -> Purpose inferred from name/context
- scripts/generate_research_plots.py -> plot_performance -> Purpose inferred from name/context

## scripts/init_postgres_db.py
- scripts/init_postgres_db.py -> main -> Purpose inferred from name/context

## scripts/list_gemini_models.py
- No functions/classes found

## scripts/migrate_db.py
- scripts/migrate_db.py -> migrate -> Production-grade migration script.

## scripts/run_pdf_test.py
- scripts/run_pdf_test.py -> run_test -> Purpose inferred from name/context

## scripts/test_load_graph.py
- No functions/classes found

## scripts/test_model_names.py
- No functions/classes found

## src/__init__.py
- No functions/classes found

## src/community/__init__.py
- No functions/classes found

## src/community/base.py
- src/community/base.py -> CommunityDetector -> Abstract community detector.
- src/community/base.py -> CommunityDetector.detect -> Assign community IDs to nodes.
- src/community/base.py -> CommunityDetector.get_name -> Return short identifier used in experiment logs and reports.
- src/community/base.py -> CommunityDetector.apply -> Run detection and apply results to the graph.

## src/community/detectors.py
- src/community/detectors.py -> LeidenDetector -> Standard Leiden algorithm using structural modularity.
- src/community/detectors.py -> LeidenDetector.__init__ -> Purpose inferred from name/context
- src/community/detectors.py -> LeidenDetector.get_name -> Purpose inferred from name/context
- src/community/detectors.py -> LeidenDetector.detect -> Purpose inferred from name/context
- src/community/detectors.py -> LeidenDetector._fallback_connected_components -> Fallback: use connected components as communities.
- src/community/detectors.py -> CWLeidenDetector -> Contribution 2a: Confidence-Weighted Leiden.
- src/community/detectors.py -> CWLeidenDetector.__init__ -> Purpose inferred from name/context
- src/community/detectors.py -> CWLeidenDetector.get_name -> Purpose inferred from name/context
- src/community/detectors.py -> CWLeidenDetector.detect -> Purpose inferred from name/context
- src/community/detectors.py -> RLMCommunityDetector -> Contribution 2b: RLM-Guided Semantic Community Detection.
- src/community/detectors.py -> RLMCommunityDetector.__init__ -> Purpose inferred from name/context
- src/community/detectors.py -> RLMCommunityDetector.get_name -> Purpose inferred from name/context
- src/community/detectors.py -> RLMCommunityDetector.detect -> Run LLM-based community detection synchronously.
- src/community/detectors.py -> RLMCommunityDetector._detect_async -> Purpose inferred from name/context
- src/community/detectors.py -> RLMCommunityDetector._build_neighborhood_description -> Build a text description of each entity's neighborhood.
- src/community/detectors.py -> RLMCommunityDetector._parse_community_response -> Parse LLM community assignment response.
- src/community/detectors.py -> build_community_detector -> Factory function: instantiate the correct detector from config.

## src/evaluation/__init__.py
- No functions/classes found

## src/evaluation/metrics.py
- src/evaluation/metrics.py -> normalize_answer -> Purpose inferred from name/context
- src/evaluation/metrics.py -> exact_match -> Purpose inferred from name/context
- src/evaluation/metrics.py -> token_f1 -> Purpose inferred from name/context
- src/evaluation/metrics.py -> rouge_l -> Purpose inferred from name/context
- src/evaluation/metrics.py -> _lcs_length -> Purpose inferred from name/context
- src/evaluation/metrics.py -> evaluate_answer -> Purpose inferred from name/context
- src/evaluation/metrics.py -> QueryResult -> Purpose inferred from name/context
- src/evaluation/metrics.py -> QueryResult.to_dict -> Purpose inferred from name/context
- src/evaluation/metrics.py -> aggregate_results -> Purpose inferred from name/context
- src/evaluation/metrics.py -> compute_community_coherence -> Mean pairwise cosine similarity within each community.
- src/evaluation/metrics.py -> compute_weighted_modularity -> Purpose inferred from name/context
- src/evaluation/metrics.py -> GraphQualityReport -> Purpose inferred from name/context
- src/evaluation/metrics.py -> GraphQualityReport.to_dict -> Purpose inferred from name/context
- src/evaluation/metrics.py -> evaluate_graph_quality -> Purpose inferred from name/context

## src/graph/__init__.py
- No functions/classes found

## src/graph/knowledge_graph.py
- src/graph/knowledge_graph.py -> Triple -> A single extracted knowledge triple.
- src/graph/knowledge_graph.py -> Triple.to_text -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> NodeData -> Data stored on each graph node.
- src/graph/knowledge_graph.py -> KnowledgeGraph -> Confidence-weighted, community-annotated Knowledge Graph.
- src/graph/knowledge_graph.py -> KnowledgeGraph.__init__ -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.add_triple -> Add a triple to the graph. Creates nodes if they don't exist.
- src/graph/knowledge_graph.py -> KnowledgeGraph.add_triples -> Batch add triples.
- src/graph/knowledge_graph.py -> KnowledgeGraph.set_node_embedding -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.set_community -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_neighbors -> Return neighbors of an entity, optionally filtered by confidence.
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_path -> Find shortest path between two entities.
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_community -> Return the community ID of an entity, or -1 if unassigned.
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_community_members -> Return all entities in a given community.
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_subgraph -> Extract a subgraph centered on given entities up to `depth` hops.
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_high_confidence_triples -> Return all triples above a confidence threshold.
- src/graph/knowledge_graph.py -> KnowledgeGraph.entity_exists -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_all_entities -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.get_all_communities -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.save -> Save graph to disk using JSON.
- src/graph/knowledge_graph.py -> KnowledgeGraph.load -> Load graph from disk using JSON.
- src/graph/knowledge_graph.py -> KnowledgeGraph.to_networkx -> Return raw NetworkX graph (for community algorithms).
- src/graph/knowledge_graph.py -> KnowledgeGraph._update_stats -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.summary -> Purpose inferred from name/context
- src/graph/knowledge_graph.py -> KnowledgeGraph.__repr__ -> Purpose inferred from name/context

## src/ingestion/__init__.py
- No functions/classes found

## src/ingestion/confidence.py
- src/ingestion/confidence.py -> ConfidenceResult -> Purpose inferred from name/context
- src/ingestion/confidence.py -> ConfidenceScorer -> Hybrid confidence scorer with three configurable modes.
- src/ingestion/confidence.py -> ConfidenceScorer.__init__ -> Purpose inferred from name/context
- src/ingestion/confidence.py -> ConfidenceScorer._composite -> Purpose inferred from name/context
- src/ingestion/confidence.py -> ConfidenceScorer._rule_score -> Fast rule-based scoring. No LLM calls.
- src/ingestion/confidence.py -> ConfidenceScorer._llm_score_batch -> Score a batch of triples in one LLM call.
- src/ingestion/confidence.py -> ConfidenceScorer._parse_batch -> Purpose inferred from name/context
- src/ingestion/confidence.py -> ConfidenceScorer.score_batch -> Score triples according to the configured mode.
- src/ingestion/confidence.py -> ConfidenceScorer.score_batch_sync -> Synchronous wrapper.

## src/ingestion/extractor.py
- src/ingestion/extractor.py -> LLMExtractor -> LLM-based triple extraction.
- src/ingestion/extractor.py -> LLMExtractor.__init__ -> Purpose inferred from name/context
- src/ingestion/extractor.py -> LLMExtractor._get_llm -> Lazy-load LLM client.
- src/ingestion/extractor.py -> LLMExtractor.extract_from_text -> Extract triples from text using LLM.
- src/ingestion/extractor.py -> LLMExtractor._parse_triples -> Parse JSON array of triples from LLM response.
- src/ingestion/extractor.py -> REBELExtractor -> REBEL-based relation extraction.
- src/ingestion/extractor.py -> REBELExtractor.__init__ -> Purpose inferred from name/context
- src/ingestion/extractor.py -> REBELExtractor._resolve_device -> Purpose inferred from name/context
- src/ingestion/extractor.py -> REBELExtractor._load -> Purpose inferred from name/context
- src/ingestion/extractor.py -> REBELExtractor.extract_from_text -> Purpose inferred from name/context
- src/ingestion/extractor.py -> REBELExtractor._parse_rebel_output -> Purpose inferred from name/context
- src/ingestion/extractor.py -> SpaCyExtractor -> spaCy dependency parsing fallback.
- src/ingestion/extractor.py -> SpaCyExtractor.__init__ -> Purpose inferred from name/context
- src/ingestion/extractor.py -> SpaCyExtractor._load -> Purpose inferred from name/context
- src/ingestion/extractor.py -> SpaCyExtractor.extract_from_text -> Purpose inferred from name/context
- src/ingestion/extractor.py -> TripleExtractor -> Unified extractor. Selects backend based on config.ingestion.extractor.
- src/ingestion/extractor.py -> TripleExtractor.__init__ -> Purpose inferred from name/context
- src/ingestion/extractor.py -> TripleExtractor.extract_from_chunk -> Purpose inferred from name/context
- src/ingestion/extractor.py -> TripleExtractor.extract_from_chunks -> Parallel extraction using asyncio.gather for speed.

## src/ingestion/graph_builder.py
- src/ingestion/graph_builder.py -> GraphBuilder -> Builds a KnowledgeGraph from triples and populates embeddings.
- src/ingestion/graph_builder.py -> GraphBuilder.__init__ -> Purpose inferred from name/context
- src/ingestion/graph_builder.py -> GraphBuilder.build -> Construct a KnowledgeGraph from a list of triples.
- src/ingestion/graph_builder.py -> GraphBuilder._embed_and_store -> Embed entity labels and register them in the vector store.
- src/ingestion/graph_builder.py -> GraphBuilder.update_embeddings_after_community -> Refresh vector store metadata after community detection is complete.

## src/ingestion/loader.py
- src/ingestion/loader.py -> DocumentChunk -> A single chunk of text from a document.
- src/ingestion/loader.py -> DocumentLoader -> Load documents from file paths or raw strings.
- src/ingestion/loader.py -> DocumentLoader.load_file -> Purpose inferred from name/context
- src/ingestion/loader.py -> DocumentLoader._load_pdf -> Try PyMuPDF first (best for ArXiv/LaTeX papers),
- src/ingestion/loader.py -> DocumentLoader.load_texts -> Return list of (text, source_name) pairs.
- src/ingestion/loader.py -> Chunker -> Splits documents into overlapping text chunks.
- src/ingestion/loader.py -> Chunker.__init__ -> Purpose inferred from name/context
- src/ingestion/loader.py -> Chunker.chunk_text -> Split text into overlapping chunks.
- src/ingestion/loader.py -> Chunker._clean_pdf_text -> Clean common PDF extraction artifacts:
- src/ingestion/loader.py -> Chunker.chunk_documents -> Chunk a list of (text, source) pairs.

## src/pipeline.py
- src/pipeline.py -> IngestResult -> Purpose inferred from name/context
- src/pipeline.py -> Pipeline -> Full RLM-GraphRAG pipeline for one experimental variant.
- src/pipeline.py -> Pipeline.__init__ -> Purpose inferred from name/context
- src/pipeline.py -> Pipeline._build_traverser -> Purpose inferred from name/context
- src/pipeline.py -> Pipeline.from_config -> Construct pipeline from AppConfig. Preferred factory method.
- src/pipeline.py -> Pipeline.ingest -> Full ingestion pipeline: (text, source) pairs → KG with communities.
- src/pipeline.py -> Pipeline.query -> Full query pipeline: question → grounded answer with evaluation metrics.

## src/retrieval/__init__.py
- No functions/classes found

## src/retrieval/answer_generator.py
- src/retrieval/answer_generator.py -> GeneratedAnswer -> Purpose inferred from name/context
- src/retrieval/answer_generator.py -> AnswerGenerator -> Generates answers from context using the configured LLM.
- src/retrieval/answer_generator.py -> AnswerGenerator.__init__ -> Purpose inferred from name/context
- src/retrieval/answer_generator.py -> AnswerGenerator.generate -> Generate answer given a question and context string.
- src/retrieval/answer_generator.py -> AnswerGenerator.generate_sync -> Purpose inferred from name/context

## src/retrieval/context_assembler.py
- src/retrieval/context_assembler.py -> ContextAssembler -> Assembles a text context from retrieved triples.
- src/retrieval/context_assembler.py -> ContextAssembler.__init__ -> Purpose inferred from name/context
- src/retrieval/context_assembler.py -> ContextAssembler.assemble -> Build a context string from traversal results.
- src/retrieval/context_assembler.py -> ContextAssembler._deduplicate -> Remove near-duplicate triples using text similarity.
- src/retrieval/context_assembler.py -> QAResult -> Complete result for one query.
- src/retrieval/context_assembler.py -> QAResult.__post_init__ -> Purpose inferred from name/context
- src/retrieval/context_assembler.py -> AnswerGenerator -> Generates answers by combining retrieved context with an LLM call.
- src/retrieval/context_assembler.py -> AnswerGenerator.__init__ -> Purpose inferred from name/context
- src/retrieval/context_assembler.py -> AnswerGenerator.generate -> Generate an answer given query and context.
- src/retrieval/context_assembler.py -> AnswerGenerator.generate_sync -> Purpose inferred from name/context

## src/retrieval/retrieval.py
- src/retrieval/retrieval.py -> SeedEntityLinker -> Links query text to seed entities in the KG via vector similarity.
- src/retrieval/retrieval.py -> SeedEntityLinker.__init__ -> Purpose inferred from name/context
- src/retrieval/retrieval.py -> SeedEntityLinker.find_seeds -> Purpose inferred from name/context
- src/retrieval/retrieval.py -> ContextAssembler -> Assembles deduplicated context string from traversal results.
- src/retrieval/retrieval.py -> ContextAssembler.__init__ -> Purpose inferred from name/context
- src/retrieval/retrieval.py -> ContextAssembler.assemble -> Purpose inferred from name/context
- src/retrieval/retrieval.py -> ContextAssembler._near_dup -> Purpose inferred from name/context

## src/retrieval/seed_linker.py
- src/retrieval/seed_linker.py -> SeedEntityLinker -> Links a natural-language query to seed entities in the graph
- src/retrieval/seed_linker.py -> SeedEntityLinker.__init__ -> Purpose inferred from name/context
- src/retrieval/seed_linker.py -> SeedEntityLinker.link -> Find the most relevant seed entities for a query.

## src/traversal/__init__.py
- No functions/classes found

## src/traversal/base.py
- src/traversal/base.py -> TraversalResult -> Result from any traversal strategy.
- src/traversal/base.py -> TraversalResult.to_context_text -> Serialize triples to text context for LLM consumption.
- src/traversal/base.py -> Traverser -> Abstract traversal strategy.
- src/traversal/base.py -> Traverser.traverse -> Traverse the graph starting from seed entities.
- src/traversal/base.py -> Traverser.get_name -> Purpose inferred from name/context
- src/traversal/base.py -> FixedHopTraverser -> Baseline K-hop traversal.
- src/traversal/base.py -> FixedHopTraverser.__init__ -> Purpose inferred from name/context
- src/traversal/base.py -> FixedHopTraverser.get_name -> Purpose inferred from name/context
- src/traversal/base.py -> FixedHopTraverser.traverse -> Purpose inferred from name/context

## src/traversal/parallel_dispatcher.py
- src/traversal/parallel_dispatcher.py -> ConvergenceScore -> Convergence information for a single node.
- src/traversal/parallel_dispatcher.py -> ParallelTraversalResult -> Extended result with convergence data.
- src/traversal/parallel_dispatcher.py -> ConvergenceScorer -> Computes convergence scores from parallel traversal results.
- src/traversal/parallel_dispatcher.py -> ConvergenceScorer.__init__ -> Purpose inferred from name/context
- src/traversal/parallel_dispatcher.py -> ConvergenceScorer.score -> Score all nodes by how many traversal paths reached them.
- src/traversal/parallel_dispatcher.py -> ParallelDispatcher -> Contribution 4: Multi-Entity Parallel Traversal with Convergence Scoring.
- src/traversal/parallel_dispatcher.py -> ParallelDispatcher.__init__ -> Purpose inferred from name/context
- src/traversal/parallel_dispatcher.py -> ParallelDispatcher.get_name -> Purpose inferred from name/context
- src/traversal/parallel_dispatcher.py -> ParallelDispatcher.traverse -> Synchronous entry point.
- src/traversal/parallel_dispatcher.py -> ParallelDispatcher._parallel_traverse -> Core parallel traversal logic.
- src/traversal/parallel_dispatcher.py -> ParallelDispatcher._async_single_traverse -> Async wrapper for the single traverser.

## src/traversal/rlm_traverser.py
- src/traversal/rlm_traverser.py -> GraphREPL -> A restricted Python execution environment that exposes
- src/traversal/rlm_traverser.py -> GraphREPL.__init__ -> Purpose inferred from name/context
- src/traversal/rlm_traverser.py -> GraphREPL.execute -> Execute safe graph operations in the graph context.
- src/traversal/rlm_traverser.py -> GraphREPL.get_state_summary -> Return a brief summary of current state for the LLM prompt.
- src/traversal/rlm_traverser.py -> RLMTraverser -> Contribution 3: RLM-Guided Graph Traversal.
- src/traversal/rlm_traverser.py -> RLMTraverser.__init__ -> Purpose inferred from name/context
- src/traversal/rlm_traverser.py -> RLMTraverser.get_name -> Purpose inferred from name/context
- src/traversal/rlm_traverser.py -> RLMTraverser.traverse -> Synchronous wrapper for async RLM traversal.
- src/traversal/rlm_traverser.py -> RLMTraverser._traverse_async -> Core async RLM traversal loop.
- src/traversal/rlm_traverser.py -> RLMTraverser._extract_code -> Extract Python code block from LLM response.

## src/utils/__init__.py
- No functions/classes found

## src/utils/config.py
- src/utils/config.py -> LLMConfig -> Purpose inferred from name/context
- src/utils/config.py -> EmbeddingsConfig -> Purpose inferred from name/context
- src/utils/config.py -> IngestionConfig -> Purpose inferred from name/context
- src/utils/config.py -> ConfidenceAxesConfig -> Purpose inferred from name/context
- src/utils/config.py -> ConfidenceConfig -> Purpose inferred from name/context
- src/utils/config.py -> LeidenConfig -> Purpose inferred from name/context
- src/utils/config.py -> CWLeidenConfig -> Purpose inferred from name/context
- src/utils/config.py -> RLMCommunityConfig -> Purpose inferred from name/context
- src/utils/config.py -> CommunityConfig -> Purpose inferred from name/context
- src/utils/config.py -> FixedHopConfig -> Purpose inferred from name/context
- src/utils/config.py -> RLMTraversalConfig -> Purpose inferred from name/context
- src/utils/config.py -> TraversalConfig -> Purpose inferred from name/context
- src/utils/config.py -> ParallelConfig -> Purpose inferred from name/context
- src/utils/config.py -> VectorStoreConfig -> Purpose inferred from name/context
- src/utils/config.py -> RetrievalConfig -> Purpose inferred from name/context
- src/utils/config.py -> AnswerGenerationConfig -> Purpose inferred from name/context
- src/utils/config.py -> EvaluationConfig -> Purpose inferred from name/context
- src/utils/config.py -> LoggingConfig -> Purpose inferred from name/context
- src/utils/config.py -> ProjectConfig -> Purpose inferred from name/context
- src/utils/config.py -> AppConfig -> Purpose inferred from name/context
- src/utils/config.py -> AppConfig.resolve_env_vars -> Override with environment variable values if set.
- src/utils/config.py -> _deep_merge -> Recursively merge override into base.
- src/utils/config.py -> load_config -> Load and merge configuration from YAML files.
- src/utils/config.py -> load_config_for_variant -> Convenience loader: resolves variant path by name.

## src/utils/llm_client.py
- src/utils/llm_client.py -> LLMResponse -> Purpose inferred from name/context
- src/utils/llm_client.py -> CostTracker -> Purpose inferred from name/context
- src/utils/llm_client.py -> CostTracker.record -> Purpose inferred from name/context
- src/utils/llm_client.py -> CostTracker.summary -> Purpose inferred from name/context
- src/utils/llm_client.py -> LLMClient -> Unified LLM client. Instantiate once, call generate() everywhere.
- src/utils/llm_client.py -> LLMClient.__init__ -> Purpose inferred from name/context
- src/utils/llm_client.py -> LLMClient._init_client -> Purpose inferred from name/context
- src/utils/llm_client.py -> LLMClient.generate -> Generate a completion. Falls back gracefully.
- src/utils/llm_client.py -> LLMClient._dispatch -> Purpose inferred from name/context
- src/utils/llm_client.py -> LLMClient._call_gemini -> Call Gemini via loop.run_in_executor for async compatibility.
- src/utils/llm_client.py -> LLMClient._call_ollama -> Call Ollama via its async interface (run sync in executor).
- src/utils/llm_client.py -> LLMClient._call_groq -> Purpose inferred from name/context
- src/utils/llm_client.py -> LLMClient._call_openai -> Purpose inferred from name/context
- src/utils/llm_client.py -> LLMClient._call_anthropic -> Purpose inferred from name/context
- src/utils/llm_client.py -> LLMClient.generate_sync -> Synchronous wrapper for non-async contexts.

## src/utils/logger.py
- src/utils/logger.py -> setup_logging -> Configure structlog for the entire application.
- src/utils/logger.py -> get_logger -> Return a named structured logger.
- src/utils/logger.py -> ExperimentLogger -> Writes per-query experiment records to a JSONL file.
- src/utils/logger.py -> ExperimentLogger.__init__ -> Purpose inferred from name/context
- src/utils/logger.py -> ExperimentLogger.record -> Write one record to the JSONL log.
- src/utils/logger.py -> ExperimentLogger.read_all -> Read all records from the JSONL file.

## src/utils/vector_store.py
- src/utils/vector_store.py -> SearchResult -> Purpose inferred from name/context
- src/utils/vector_store.py -> VectorStore -> ChromaDB-backed entity vector store.
- src/utils/vector_store.py -> VectorStore.__init__ -> Purpose inferred from name/context
- src/utils/vector_store.py -> VectorStore._init -> Purpose inferred from name/context
- src/utils/vector_store.py -> VectorStore.add_entities -> Add entities to the vector store.
- src/utils/vector_store.py -> VectorStore.search -> Find the top-k most similar entities to the query embedding.
- src/utils/vector_store.py -> VectorStore.count -> Return total number of stored entities.
- src/utils/vector_store.py -> VectorStore.clear -> Remove all entities from the collection.
- src/utils/vector_store.py -> EmbeddingModel -> Wrapper for sentence-transformers embeddings.
- src/utils/vector_store.py -> EmbeddingModel.__init__ -> Purpose inferred from name/context
- src/utils/vector_store.py -> EmbeddingModel._resolve_device -> Purpose inferred from name/context
- src/utils/vector_store.py -> EmbeddingModel._load -> Purpose inferred from name/context
- src/utils/vector_store.py -> EmbeddingModel.encode -> Encode a list of texts to embeddings.
- src/utils/vector_store.py -> EmbeddingModel.encode_single -> Encode a single text and return as list.
