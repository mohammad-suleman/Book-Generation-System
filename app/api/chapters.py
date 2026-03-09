""" 
API endpoints for chapter generation and management
"""
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false, reportOperatorIssue=false, reportOptionalMemberAccess=false
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.constants import BookStage, NotesStatus
from app.models import Book, Outline, Chapter
from app.schemas import ChapterResponse, ChapterUpdate, ChapterGenerateRequest
from app.services.openai_service import openai_service
from app.services.workflow_service import workflow_service
from app.services.context_service import context_service
from app.services.email_service import email_service
from app.core.logging_config import get_logger

logger = get_logger("app.api.chapters")
output_logger = get_logger("app.output")

router = APIRouter()


@router.post("/books/{book_id}/chapters/{chapter_number}/generate", response_model=ChapterResponse)
async def generate_chapter(
    book_id: int,
    chapter_number: int,
    request: ChapterGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate a specific chapter"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Check if generation is allowed
    can_generate, reason = workflow_service.can_generate_chapter(db, book_id, chapter_number)
    if not can_generate and not request.regenerate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )
    
    # Get outline
    outline = db.query(Outline).filter(Outline.book_id == book_id).first()
    if not outline or not outline.outline_content:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Outline must be generated before chapters"
        )
    
    # Check if chapter exists
    chapter = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number == chapter_number
    ).first()
    
    if chapter and not request.regenerate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chapter {chapter_number} already exists. Use regenerate=true to update it."
        )
    
    try:
        # Get context from previous chapters
        previous_context = context_service.get_previous_chapters_context(
            db,
            book_id,
            chapter_number
        )
        
        # Generate chapter
        logger.info(f"Generating chapter {chapter_number} for book {book_id}: '{book.title}'")
        chapter_title, chapter_content = openai_service.generate_chapter(
            chapter_number=chapter_number,
            book_title=book.title,
            outline=outline.outline_content,
            previous_summaries=previous_context,
            chapter_notes=request.notes
        )
        logger.info(f"Chapter {chapter_number} generated: '{chapter_title}' ({len(chapter_content)} chars)")
        output_logger.info(f"CHAPTER | Book {book_id} - Chapter {chapter_number}: '{chapter_title}' ({len(chapter_content)} chars)")
        
        # Generate summary for context chaining (temporarily disabled for debugging)
        # summary = openai_service.generate_summary(chapter_content, chapter_title)
        summary =  f"Summary of Chapter {chapter_number}: {chapter_title}"  # Placeholder
        
        # Create or update chapter
        if chapter:
            chapter.title = chapter_title
            chapter.content = chapter_content
            chapter.summary = summary
            chapter.regeneration_count += 1
            if request.notes:
                chapter.notes = request.notes
        else:
            chapter = Chapter(
                book_id=book_id,
                chapter_number=chapter_number,
                title=chapter_title,
                content=chapter_content,
                summary=summary,
                notes=request.notes,
                notes_status=NotesStatus.NO_NOTES_NEEDED
            )
            db.add(chapter)
        
        # Update book stage
        workflow_service.advance_book_stage(db, book_id, BookStage.CHAPTERS)
        
        db.commit()
        db.refresh(chapter)
        
        # Send notification in background
        background_tasks.add_task(
            email_service.send_chapter_generated_email,
            db,
            book_id,
            book.title,
            chapter_number
        )
        
        return chapter
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate chapter {chapter_number} for book {book_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chapter: {str(e)}"
        )


@router.get("/books/{book_id}/chapters", response_model=List[ChapterResponse])
def list_chapters(book_id: int, db: Session = Depends(get_db)):
    """List all chapters for a book"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    chapters = db.query(Chapter).filter(
        Chapter.book_id == book_id
    ).order_by(Chapter.chapter_number).all()
    
    return chapters


@router.get("/books/{book_id}/chapters/{chapter_number}", response_model=ChapterResponse)
def get_chapter(book_id: int, chapter_number: int, db: Session = Depends(get_db)):
    """Get a specific chapter"""
    chapter = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number == chapter_number
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_number} not found for book {book_id}"
        )
    
    return chapter


@router.put("/books/{book_id}/chapters/{chapter_number}/notes", response_model=ChapterResponse)
def update_chapter_notes(
    book_id: int,
    chapter_number: int,
    update: ChapterUpdate,
    db: Session = Depends(get_db)
):
    """Update chapter notes and status"""
    chapter = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number == chapter_number
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_number} not found for book {book_id}"
        )
    
    # Update fields
    if update.notes is not None:
        chapter.notes = update.notes
    
    if update.notes_status is not None:
        chapter.notes_status = update.notes_status
    
    db.commit()
    db.refresh(chapter)
    
    return chapter


@router.post("/books/{book_id}/chapters/{chapter_number}/regenerate", response_model=ChapterResponse)
async def regenerate_chapter(
    book_id: int,
    chapter_number: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Regenerate a chapter using its notes"""
    chapter = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.chapter_number == chapter_number
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_number} not found for book {book_id}"
        )
    
    if not chapter.notes:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chapter notes must be provided before regenerating"
        )
    
    book = db.query(Book).filter(Book.id == book_id).first()
    outline = db.query(Outline).filter(Outline.book_id == book_id).first()
    
    try:
        # Get context from previous chapters
        previous_context = context_service.get_previous_chapters_context(
            db,
            book_id,
            chapter_number
        )
        
        # Regenerate chapter with notes
        chapter_title, chapter_content = openai_service.generate_chapter(
            chapter_number=chapter_number,
            book_title=book.title,
            outline=outline.outline_content,
            previous_summaries=previous_context,
            chapter_notes=chapter.notes
        )
        
        # Regenerate summary
        summary = openai_service.generate_summary(chapter_content, chapter_title)
        
        # Update chapter
        chapter.title = chapter_title
        chapter.content = chapter_content
        chapter.summary = summary
        chapter.regeneration_count += 1
        
        db.commit()
        db.refresh(chapter)
        
        # Send notification
        background_tasks.add_task(
            email_service.send_chapter_generated_email,
            db,
            book_id,
            book.title,
            chapter_number
        )
        
        return chapter
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate chapter: {str(e)}"
        )
