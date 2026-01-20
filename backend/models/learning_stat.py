from sqlalchemy import Column, String, DateTime, Date, Integer, UniqueConstraint
from sqlalchemy.sql import func
import uuid

from models.database import Base


class LearningStat(Base):
    __tablename__ = "learning_stats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    
    questions_done = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    study_time = Column(Integer, default=0)  # seconds
    exams_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("date", name="uq_date"),
    )
