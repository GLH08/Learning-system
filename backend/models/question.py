from sqlalchemy import Column, String, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from models.database import Base


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    # Basic info
    type = Column(String, nullable=False)  # single/multiple/judge/essay
    difficulty = Column(String, default="medium")  # easy/medium/hard
    content = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON string
    
    # Answer and explanation
    answer = Column(Text, nullable=True)
    answer_status = Column(String, default="none")  # none/ai_pending/ai_generated/confirmed
    explanation = Column(Text, nullable=True)
    explanation_status = Column(String, default="none")
    
    # Metadata
    tags = Column(Text, nullable=True)  # JSON string
    source = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("type IN ('single', 'multiple', 'judge', 'essay')", name="check_type"),
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="check_difficulty"),
        CheckConstraint("answer_status IN ('none', 'ai_pending', 'ai_generated', 'confirmed')", name="check_answer_status"),
        CheckConstraint("explanation_status IN ('none', 'ai_pending', 'ai_generated', 'confirmed')", name="check_explanation_status"),
    )
    
    # Relationships
    category = relationship("Category", back_populates="questions")
    wrong_questions = relationship("WrongQuestion", back_populates="question", cascade="all, delete-orphan")
