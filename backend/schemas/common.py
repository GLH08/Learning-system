from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """Standard API response"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PageResponse(BaseModel, Generic[T]):
    """Paginated response"""
    items: List[T]
    total: int
    page: int
    pageSize: int
    totalPages: int


class PagedResponse(BaseModel):
    """Standard paginated API response"""
    code: int = 0
    message: str = "success"
    data: Optional[PageResponse] = None
