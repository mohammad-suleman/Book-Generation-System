"""
Pydantic schemas for Book entities
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.core.constants import BookStage


class BookBase(BaseModel):
    """Base book schema"""
    title: str = Field(..., min_length=1, max_length=500)


class BookCreate(BookBase):
    """Schema for creating a book"""
    pass


class BookResponse(BookBase):
    """Schema for book response"""
    id: int
    current_stage: BookStage
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BookWithDetails(BookResponse):
    """Schema for book with full details"""
    outline_status: Optional[str] = None
    chapters_count: int = 0
    final_draft_status: Optional[str] = None


class BookUpdate(BaseModel):
    """Schema for updating a book"""
    current_stage: Optional[BookStage] = None
