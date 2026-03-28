"""
AI Risk Detection Engine — StudyMines + eduRAG
Calculates academic risk by combining behavioral engagement and GraphRAG mastery.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User, AcademicRisk, EventLog, MasteryLog, Enrollment, Course

class RiskEngine:
    """
    Analyzes student data to predict academic failure or disengagement.
    """

    def __init__(self, db: Session):
        self.db = db

    async def analyze_student(self, user_id, course_id) -> AcademicRisk:
        """
        Calculates a Risk Score (0-100) for a student in a specific course.
        100 = Highest Risk, 0 = Safe.
        """
        # 1. Behavioral Engagement (0.4 weight)
        engagement_score = self._calculate_engagement(user_id)
        
        # 2. Cognitive Mastery (0.6 weight)
        mastery_score = self._calculate_mastery(user_id)
        
        # 3. Calculate Final Risk
        # Risk is the inverse of student performance
        risk_val = (1.0 - (mastery_score * 0.6 + engagement_score * 0.4)) * 100
        risk_val = max(0, min(100, risk_val)) # Clamp
        
        level = "low"
        if risk_val > 75: level = "critical"
        elif risk_val > 50: level = "high"
        elif risk_val > 25: level = "medium"
        
        flags = []
        if engagement_score < 0.3: flags.append("low_engagement")
        if mastery_score < 0.4: flags.append("weak_concept_mastery")
        
        # 4. Persist
        risk_record = self.db.query(AcademicRisk).filter(
            AcademicRisk.user_id == user_id,
            AcademicRisk.course_id == course_id
        ).first()
        
        if not risk_record:
            risk_record = AcademicRisk(user_id=user_id, course_id=course_id)
            self.db.add(risk_record)
        
        risk_record.risk_score = round(risk_val, 2)
        risk_record.risk_level = level
        risk_record.flags = flags
        risk_record.analysis_data = {
            "cognitive_component": round(mastery_score, 2),
            "behavioral_component": round(engagement_score, 2),
            "last_calculated": datetime.utcnow().isoformat()
        }
        
        self.db.commit()
        self.db.refresh(risk_record)
        return risk_record

    def _calculate_engagement(self, user_id) -> float:
        """Engagement based on event frequency in the last 7 days."""
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        event_count = self.db.query(EventLog).filter(
            EventLog.user_id == user_id,
            EventLog.timestamp >= seven_days_ago
        ).count()
        
        # Benchmark: 50 events per week is 'perfect' engagement (1.0)
        score = event_count / 50.0
        return min(1.0, score)

    def _calculate_mastery(self, user_id) -> float:
        """Mastery based on historical MasteryLogs."""
        avg_mastery = self.db.query(func.avg(MasteryLog.score)).filter(
            MasteryLog.user_id == user_id
        ).scalar() or 0.0
        
        return float(avg_mastery)


def update_mastery_from_quiz(db: Session, user_id, entity_id, quiz_score):
    """Bridge function to record mastery after a quiz attempt."""
    # Convert quiz percentage/score to 0-1 scale
    mastery_val = quiz_score / 100.0 if quiz_score > 1.0 else quiz_score
    
    log = MasteryLog(
        user_id=user_id,
        entity_id=entity_id,
        score=mastery_val,
        source_type="assessment"
    )
    db.add(log)
    db.commit()
    return log
