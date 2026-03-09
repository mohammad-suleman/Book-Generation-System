"""
Workflow service for managing book generation state machine and gating logic
"""
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportOperatorIssue=false
from sqlalchemy.orm import Session
from typing import Optional

from app.models import Book, Outline, Chapter, FinalDraft
from app.core.constants import BookStage, NotesStatus


class WorkflowService:
    """Service for managing workflow gating logic"""
    
    def can_generate_outline(self, db: Session, book_id: int) -> tuple[bool, Optional[str]]:
        """
        Check if outline generation is allowed.
        
        Returns:
            Tuple of (can_generate, reason_if_not)
        """
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return False, "Book not found"
        
        outline = db.query(Outline).filter(Outline.book_id == book_id).first()
        if not outline:
            return False, "Outline record not found. Please import book first."
        
        if not outline.notes_before:  # type: ignore
            return False, "notes_on_outline_before is required before generating outline"
        
        return True, None
    
    def can_proceed_from_outline(self, db: Session, book_id: int) -> tuple[bool, Optional[str]]:
        """
        Check if we can proceed from outline stage to chapter generation.
        
        Returns:
            Tuple of (can_proceed, reason_if_not)
        """
        outline = db.query(Outline).filter(Outline.book_id == book_id).first()
        if not outline:
            return False, "Outline not found"
        
        if not outline.outline_content:  # type: ignore
            return False, "Outline content not generated yet"
        
        if outline.status == NotesStatus.YES:  # type: ignore
            return False, "Waiting for outline review notes (notes_after)"
        
        if outline.status == NotesStatus.NO:  # type: ignore
            return False, "Outline review paused (status is 'no'). Set to 'no_notes_needed' or 'yes' with notes."
        
        # NotesStatus.NO_NOTES_NEEDED means we can proceed
        return True, None
    
    def can_generate_chapter(
        self,
        db: Session,
        book_id: int,
        chapter_number: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if chapter generation is allowed.
        
        Returns:
            Tuple of (can_generate, reason_if_not)
        """
        # First check if we can proceed from outline
        can_proceed, reason = self.can_proceed_from_outline(db, book_id)
        if not can_proceed:
            return False, reason
        
        # Check if previous chapter exists and is approved
        if chapter_number > 1:
            previous_chapter = db.query(Chapter).filter(
                Chapter.book_id == book_id,
                Chapter.chapter_number == chapter_number - 1
            ).first()
            
            if not previous_chapter:
                return False, f"Previous chapter (Chapter {chapter_number - 1}) must be generated first"
            
            if previous_chapter.notes_status == NotesStatus.YES:  # type: ignore
                return False, f"Waiting for notes on Chapter {chapter_number - 1}"
            
            if previous_chapter.notes_status == NotesStatus.NO:  # type: ignore
                return False, f"Chapter {chapter_number - 1} review paused. Set status to proceed."
        
        # Check if this chapter already exists
        existing_chapter = db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_number == chapter_number
        ).first()
        
        if existing_chapter and existing_chapter.content:  # type: ignore
            return False, f"Chapter {chapter_number} already exists. Use regenerate endpoint to update it."
        
        return True, None
    
    def can_compile_final(self, db: Session, book_id: int) -> tuple[bool, Optional[str]]:
        """
        Check if final compilation is allowed.
        
        Returns:
            Tuple of (can_compile, reason_if_not)
        """
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return False, "Book not found"
        
        # Check if we have chapters
        chapters = db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()
        if not chapters:
            return False, "No chapters have been generated yet"
        
        # Check if all chapters are approved
        for chapter in chapters:
            if chapter.notes_status == NotesStatus.YES:  # type: ignore
                return False, f"Waiting for notes on Chapter {chapter.chapter_number}"
            if chapter.notes_status == NotesStatus.NO:  # type: ignore
                return False, f"Chapter {chapter.chapter_number} review paused"
        
        # Check final draft status
        final_draft = db.query(FinalDraft).filter(FinalDraft.book_id == book_id).first()
        if final_draft:
            if final_draft.review_notes_status == NotesStatus.YES:  # type: ignore
                return False, "Waiting for final review notes"
            if final_draft.review_notes_status == NotesStatus.NO:  # type: ignore
                return False, "Final review paused. Set status to 'no_notes_needed' or provide notes."
        
        return True, None
    
    def advance_book_stage(self, db: Session, book_id: int, new_stage: BookStage):
        """
        Update the current stage of a book.
        
        Args:
            db: Database session
            book_id: Book ID
            new_stage: New stage to set
        """
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            book.current_stage = new_stage
            db.commit()


# Global service instance
workflow_service = WorkflowService()
