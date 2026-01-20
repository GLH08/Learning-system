from sqlalchemy import Column, String, DateTime, Integer, Text, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from models.database import Base


class Exam(Base):
    """考试记录模型"""
    __tablename__ = "exams"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 试卷信息
    title = Column(String, nullable=False)
    mode = Column(String, nullable=False)  # exam/practice/review
    
    # 配置信息
    config = Column(Text, nullable=True)  # JSON: 组卷配置
    
    # 题目信息
    question_ids = Column(Text, nullable=False)  # JSON: 题目ID列表
    total_count = Column(Integer, default=0)
    
    # 答题信息
    answers = Column(Text, nullable=True)  # JSON: 用户答案 {questionId: answer}
    
    # 评分信息
    status = Column(String, default="in_progress")  # in_progress/completed
    score = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    
    # 时间信息
    time_limit = Column(Integer, nullable=True)  # 考试时长（秒），null表示不限时
    start_time = Column(DateTime, nullable=True)
    submit_time = Column(DateTime, nullable=True)
    time_used = Column(Integer, nullable=True)  # 实际用时（秒）
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint("mode IN ('exam', 'practice', 'review')", name="check_mode"),
        CheckConstraint("status IN ('in_progress', 'completed')", name="check_status"),
    )
    
    # Relationships
    wrong_questions = relationship("WrongQuestion", back_populates="exam", cascade="all, delete-orphan")


class WrongQuestion(Base):
    """错题记录模型"""
    __tablename__ = "wrong_questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    question_id = Column(String, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(String, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    
    # 错误信息
    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    wrong_count = Column(Integer, default=1)  # 错误次数
    
    # 掌握状态
    mastered = Column(Integer, default=0)  # 0: 未掌握, 1: 已掌握
    
    last_wrong_time = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    question = relationship("Question", back_populates="wrong_questions")
    exam = relationship("Exam", back_populates="wrong_questions")
