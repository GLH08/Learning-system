from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class QuestionBase(BaseModel):
    categoryId: Optional[str] = Field(None, description="分类ID")
    type: str = Field(..., description="题型: single/multiple/judge/essay")
    difficulty: str = Field("medium", description="难度: easy/medium/hard")
    content: str = Field(..., description="题干内容")
    options: Optional[Dict[str, str]] = Field(None, description="选项")
    answer: Optional[str] = Field(None, description="答案")
    explanation: Optional[str] = Field(None, description="解析")
    tags: Optional[List[str]] = Field(None, description="标签")
    source: Optional[str] = Field(None, description="来源")


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    categoryId: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    content: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None


class QuestionResponse(QuestionBase):
    id: str
    answerStatus: str
    explanationStatus: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True


class QuestionListQuery(BaseModel):
    page: int = Field(1, ge=1)
    pageSize: int = Field(20, ge=1, le=100)
    keyword: Optional[str] = None
    categoryId: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    status: Optional[str] = None
    answerStatus: Optional[str] = None
    explanationStatus: Optional[str] = None
    sortBy: str = "createdAt"
    sortOrder: str = "desc"


class QuestionStatsResponse(BaseModel):
    total: int
    byType: Dict[str, int]
    byDifficulty: Dict[str, int]
    byStatus: Dict[str, int]
    incomplete: int
