from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func

from models.database import Base


class Setting(Base):
    __tablename__ = "settings"
    
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
