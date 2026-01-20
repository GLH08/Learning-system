"""
AI Task Model
"""
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base


class AITask(Base):
    """AI Task Model"""
    __tablename__ = "ai_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)  # answer/explanation/both/report
    status = Column(String, default="pending")  # pending/running/paused/completed/failed/cancelled
    
    # Task content
    question_ids = Column(Text)  # JSON array of question IDs
    total_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    current_question_id = Column(String)
    
    # Related entity (for report generation)
    related_id = Column(String)
    
    # Result and error
    result = Column(Text)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<AITask {self.id} {self.type} {self.status}>"
