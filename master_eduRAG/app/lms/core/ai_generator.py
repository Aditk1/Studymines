from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Upload, QuestionBank, GraphEntity
from app.llm.epf_generator import EPFGenerator
from app.llm.utils import clean_json_response
from app.utils import get_logger

logger = get_logger(__name__)

# Initializing a default generator instance
_gen = EPFGenerator()

def CognitiveAIGenerator(
    topic: str,
    context_type: str = "general", # 'general', 'document', 'mastery'
    num_items: int = 5,
    difficulty: str = "medium",
    upload_id: Optional[int] = None,
    db: Optional[Session] = None
) -> List[Dict]:
    """
    Universal AI generator for Quizzes, Exams, and Lesson Plans.
    
    Args:
        topic: The primary subject (e.g., 'Quantum Physics').
        context_type: Affects the source of knowledge.
        num_items: Total questions to generate.
        difficulty: cognitive level (easy, medium, hard).
        upload_id: If document-specific, fetch text from the upload.
        db: Database session for context retrieval.
        
    Returns:
        List of generated items (questions, answers, options).
    """
    system_context = ""
    
    # 1. ENRICH CONTEXT
    if context_type == "document" and upload_id and db:
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if upload and upload.study_package:
            # Extract key concepts from existing package for grounding
            pkg = json.loads(upload.study_package)
            system_context = f"Based on this document: {pkg.get('topic', 'N/A')}. Context snippet: {pkg.get('summary', '')[:2000]}"
    
    elif context_type == "mastery" and db:
        # Fetch weak concepts from the GraphRAG layer
        weak_entities = db.query(GraphEntity).filter(GraphEntity.mastery_score < 0.5).limit(3).all()
        if weak_entities:
            concepts = ", ".join([e.entity_name for e in weak_entities])
            system_context = f"Focus on these challenging student concepts: {concepts}."

    # 2. CONSTRUCT PROMPT
    prompt = f"""
    You are an expert academic examiner. Generate {num_items} high-quality Multiple Choice Questions (MCQs) for the topic: '{topic}'.
    Difficulty: {difficulty}.
    {system_context}
    
    Return ONLY a valid JSON list in this EXACT format:
    [
      {{
        "question": "Clear and concise question text?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "The correct option exactly as written",
        "explanation": "Brief pedagogical explanation why this is correct.",
        "bloom_level": "apply"
      }}
    ]
    Do not include any conversational text before or after the JSON.
    """

    # 3. CALL LLM (GEMINI -> GROQ -> OLLAMA)
    try:
        result = _gen._generate_content(prompt)
        # Clean and parse response
        generated_data = clean_json_response(result)
        if isinstance(generated_data, list) and len(generated_data) > 0:
            return generated_data
                
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        
    # Fallback to static dummy for demo if LLM is offline or fails to generate valid json
    logger.warning(f"Utilizing fallback (status {response.status_code if 'response' in locals() else 'error'})")
    return [
        {
            "question": f"What is a core principle of {topic}? (Fallback Q{i+1})",
            "options": [f"{topic} Option A", f"{topic} Option B", f"{topic} Option C", f"{topic} Option D"],
            "answer": f"{topic} Option A",
            "explanation": f"This is an auto-generated fallback question about {topic}. The AI model was unavailable.",
            "bloom_level": "remember"
        }
        for i in range(num_items)
    ]
