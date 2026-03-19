"""
Educational Prompt Framework (EPF) for content generation.
Uses Gemini to generate leveled summaries, concepts, flashcards, and questions.
"""

import json
from typing import Dict, List, Optional
import google.generativeai as genai
from app.config import DEFAULT_MODEL
from app.llm.utils import clean_json_response, retry_with_backoff


class EPFGenerator:
    """Generates educational outputs using the Educational Prompt Framework."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize EPF generator with Gemini API.
        
        Args:
            api_key: Gemini API key (or use GOOGLE_API_KEY env var).
        """
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)

    @retry_with_backoff(retries=5)
    def _generate_content(self, prompt: str):
        """Helper to call Gemini with retry logic."""
        return self.model.generate_content(prompt)

    def generate_outputs(
        self,
        text: str,
        student_level: str = "undergraduate",
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict:
        """
        Generate all four educational outputs: summary, concepts, flashcards, questions.
        
        Args:
            text: Content to process.
            student_level: Target level (high_school, undergraduate, postgraduate).
            subject: Subject for context.
            topic: Topic for context.
            
        Returns:
            Dictionary with all outputs.
        """
        context = ""
        if subject:
            context += f"Subject: {subject}\n"
        if topic:
            context += f"Topic: {topic}\n"

        prompt = f"""
You are an expert educational content specialist. Generate comprehensive study materials.

{context}
Student Level: {student_level}

Content to Process:
{text}

Generate the FOLLOWING in JSON format:

1. LEVELED SUMMARY: A concise summary adapted to {student_level} comprehension level.
2. KEY CONCEPTS: List of 5+ core concepts with brief explanations.
3. FLASHCARDS: 6+ question-answer pairs for active recall, with difficulty tags.
4. EXAM QUESTIONS: 4+ questions covering Bloom's taxonomy (recall, understand, apply, analyze) with difficulty and model answers.

Respond ONLY with valid JSON:
{{
    "summary": {{
        "title": "Summary Title",
        "content": "Leveled summary text",
        "length_level": "brief|moderate|detailed"
    }},
    "concepts": [
        {{
            "name": "Concept Name",
            "definition": "Brief definition",
            "importance": "high|medium|low"
        }}
    ],
    "flashcards": [
        {{
            "question": "Question text",
            "answer": "Answer text",
            "difficulty": "easy|medium|hard",
            "tags": ["tag1", "tag2"]
        }}
    ],
    "questions": [
        {{
            "question": "Question text",
            "question_type": "recall|understand|apply|analyze",
            "difficulty": "easy|medium|hard",
            "model_answer": "Expected answer",
            "explanation": "Why this is correct"
        }}
    ]
}}
"""

        try:
            response = self._generate_content(prompt)
            result = clean_json_response(response.text)
            return {
                "success": True,
                "data": result,
                "student_level": student_level
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }

    def generate_summary(
        self,
        text: str,
        student_level: str = "undergraduate"
    ) -> Dict:
        """Generate only leveled summary."""
        prompt = f"""
Generate a concise summary of the following text, adapted for {student_level} level comprehension.
Keep it clear, concise, and pedagogically useful.

Text:
{text}

Respond with JSON:
{{
    "title": "Summary title",
    "content": "Summary text",
    "length_level": "brief|moderate|detailed"
}}
"""
        try:
            response = self._generate_content(prompt)
            return clean_json_response(response.text)
        except Exception as e:
            return {"error": str(e)}

    def generate_flashcards(self, text: str, topic: Optional[str] = None) -> List[Dict]:
        """Generate flashcards for the content."""
        topic_context = f" for {topic}" if topic else ""
        
        prompt = f"""
Create 6+ study flashcards{topic_context} from the following content. Each flashcard should test core concepts.

Content:
{text}

Respond with JSON:
{{
    "flashcards": [
        {{
            "question": "Question text",
            "answer": "Answer text",
            "difficulty": "easy|medium|hard",
            "tags": ["relevant", "tags"]
        }}
    ]
}}
"""
        try:
            response = self._generate_content(prompt)
            result = clean_json_response(response.text)
            return result.get("flashcards", [])
        except Exception as e:
            return []

    def generate_questions(self, text: str, num_questions: int = 4) -> List[Dict]:
        """Generate exam questions covering Bloom's taxonomy."""
        prompt = f"""
Create {num_questions} exam questions covering different cognitive levels (recall, understand, apply, analyze).
Include difficulty level and model answers.

Content:
{text}

Respond with JSON:
{{
    "questions": [
        {{
            "question": "Question text",
            "question_type": "recall|understand|apply|analyze",
            "difficulty": "easy|medium|hard",
            "model_answer": "Expected answer",
            "explanation": "Why this is the correct answer"
        }}
    ]
}}
"""
        try:
            response = self._generate_content(prompt)
            result = clean_json_response(response.text)
            return result.get("questions", [])
        except Exception as e:
            return []


def generate_study_package(
    text: str,
    student_level: str = "undergraduate",
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Convenience function to generate complete study package.
    
    Args:
        text: Content to process.
        student_level: Student level for adaptation.
        subject: Subject for context.
        topic: Topic for context.
        api_key: Optional Gemini API key.
        
    Returns:
        Complete study package with all outputs.
    """
    generator = EPFGenerator(api_key)
    return generator.generate_outputs(text, student_level, subject, topic)
