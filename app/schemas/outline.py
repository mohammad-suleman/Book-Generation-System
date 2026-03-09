"""
Pydantic schemas for Outline entities
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.core.constants import NotesStatus


class OutlineBase(BaseModel):
    """Base outline schema"""
    notes_before: Optional[str] = None
    notes_after: Optional[str] = None


class OutlineCreate(OutlineBase):
    """Schema for creating an outline"""
    book_id: int


class OutlineResponse(OutlineBase):
    """Schema for outline response"""
    id: int
    book_id: int
    outline_content: Optional[str] = None
    status: NotesStatus
    regeneration_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OutlineUpdate(BaseModel):
    """Schema for updating an outline"""
    notes_after: Optional[str] = None
    status: Optional[NotesStatus] = None


class OutlineGenerateRequest(BaseModel):
    """Schema for outline generation request"""
    regenerate: bool = Field(default=False, description="Whether to regenerate existing outline")
