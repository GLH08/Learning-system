from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., description="分类名称")
    parentId: Optional[str] = Field(None, description="父分类ID")
    description: Optional[str] = Field(None, description="分类描述")
    sortOrder: int = Field(0, description="排序顺序")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parentId: Optional[str] = None
    description: Optional[str] = None
    sortOrder: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: str
    questionCount: int = 0
    children: List['CategoryResponse'] = []
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True


# For recursive model
CategoryResponse.model_rebuild()
