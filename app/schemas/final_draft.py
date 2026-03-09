"""
Pydantic schemas for FinalDraft entities
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.core.constants import NotesStatus, OutputStatus


class FinalDraftBase(BaseModel):
    """Base final draft schema"""
    final_notes: Optional[str] = None


class FinalDraftCreate(FinalDraftBase):
    """Schema for creating a final draft"""
    book_id: int


class FinalDraftResponse(FinalDraftBase):
    """Schema for final draft response"""
    id: int
    book_id: int
    review_notes_status: NotesStatus
    output_status: OutputStatus
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FinalDraftUpdate(BaseModel):
    """Schema for updating a final draft"""
    review_notes_status: Optional[NotesStatus] = None
    final_notes: Optional[str] = None


class CompileRequest(BaseModel):
    """Schema for compilation request"""
    force: bool = Field(default=False, description="Force compilation even if checks fail")
