"""
Pydantic schemas for Chapter entities
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.core.constants import NotesStatus


class ChapterBase(BaseModel):
    """Base chapter schema"""
    chapter_number: int = Field(..., ge=1)
    notes: Optional[str] = None


class ChapterCreate(ChapterBase):
    """Schema for creating a chapter"""
    book_id: int


class ChapterResponse(ChapterBase):
    """Schema for chapter response"""
    id: int
    book_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    notes_status: NotesStatus
    regeneration_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChapterUpdate(BaseModel):
    """Schema for updating a chapter"""
    notes: Optional[str] = None
    notes_status: Optional[NotesStatus] = None


class ChapterGenerateRequest(BaseModel):
    """Schema for chapter generation request"""
    regenerate: bool = Field(default=False, description="Whether to regenerate existing chapter")
    notes: Optional[str] = Field(default=None, description="Optional notes to guide chapter generation")
