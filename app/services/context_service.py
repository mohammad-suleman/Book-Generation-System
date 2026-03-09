"""
Context service for managing chapter summaries and context chaining
"""
# pyright: reportAttributeAccessIssue=false, reportOperatorIssue=false
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import Chapter
from app.core.constants import MAX_CONTEXT_CHAPTERS


class ContextService:
    """Service for managing chapter context and summaries"""
    
    def get_previous_chapters_context(
        self,
        db: Session,
        book_id: int,
        current_chapter_num: int
    ) -> Optional[str]:
        """
        Retrieve summaries of previous chapters for context.
        
        Args:
            db: Database session
            book_id: Book ID
            current_chapter_num: Current chapter number
        
        Returns:
            Formatted string with previous chapter summaries, or None if no previous chapters
        """
        if current_chapter_num <= 1:
            return None
        
        # Get previous chapters (limit to MAX_CONTEXT_CHAPTERS most recent)
        start_chapter = max(1, current_chapter_num - MAX_CONTEXT_CHAPTERS)
        
        previous_chapters = db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_number >= start_chapter,
            Chapter.chapter_number < current_chapter_num
        ).order_by(Chapter.chapter_number).all()
        
        if not previous_chapters:
            return None
        
        return self.build_context_prompt(previous_chapters)
    
    def build_context_prompt(self, chapters: List[Chapter]) -> str:
        """
        Build a formatted context prompt from chapter summaries.
        
        Args:
            chapters: List of Chapter objects with summaries
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for chapter in chapters:
            if chapter.summary:  # type: ignore
                context_parts.append(
                    f"Chapter {chapter.chapter_number}: {chapter.title}\nSummary: {chapter.summary}\n"
                )
        
        if not context_parts:
            return ""
        
        return "\n".join(context_parts)
    
    def get_all_chapters_for_compilation(
        self,
        db: Session,
        book_id: int
    ) -> List[Chapter]:
        """
        Get all chapters for final compilation.
        
        Args:
            db: Database session
            book_id: Book ID
        
        Returns:
            List of chapters ordered by chapter number
        """
        return db.query(Chapter).filter(
            Chapter.book_id == book_id
        ).order_by(Chapter.chapter_number).all()


# Global service instance
context_service = ContextService()
