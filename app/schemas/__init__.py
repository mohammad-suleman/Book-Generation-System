"""
Pydantic schemas for API validation
"""
from app.schemas.book import BookCreate, BookResponse, BookWithDetails, BookUpdate
from app.schemas.outline import OutlineCreate, OutlineResponse, OutlineUpdate, OutlineGenerateRequest
from app.schemas.chapter import ChapterCreate, ChapterResponse, ChapterUpdate, ChapterGenerateRequest
from app.schemas.final_draft import FinalDraftCreate, FinalDraftResponse, FinalDraftUpdate, CompileRequest

__all__ = [
    "BookCreate", "BookResponse", "BookWithDetails", "BookUpdate",
    "OutlineCreate", "OutlineResponse", "OutlineUpdate", "OutlineGenerateRequest",
    "ChapterCreate", "ChapterResponse", "ChapterUpdate", "ChapterGenerateRequest",
    "FinalDraftCreate", "FinalDraftResponse", "FinalDraftUpdate", "CompileRequest"
]
