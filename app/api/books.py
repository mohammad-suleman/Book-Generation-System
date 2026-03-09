"""
API endpoints for books and outline management
"""
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false, reportOperatorIssue=false, reportOptionalMemberAccess=false
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path

from app.core.database import get_db
from app.core.constants import BookStage, NotesStatus
from app.models import Book, Outline
from app.schemas import (
    BookResponse,
    BookWithDetails,
    OutlineResponse,
    OutlineUpdate,
    OutlineGenerateRequest
)
from app.services.csv_service import csv_service
from app.services.openai_service import openai_service
from app.services.workflow_service import workflow_service
from app.services.email_service import email_service
from app.core.logging_config import get_logger

logger = get_logger("app.api.books")
output_logger = get_logger("app.output")

router = APIRouter()


@router.post("/books/import", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def import_book(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import a book from CSV file.
    
    CSV must contain columns:
    - title (required)
    - notes_on_outline_before (required)
    - notes_on_outline_after (optional)
    - status_outline_notes (optional)
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    # Save uploaded file temporarily
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / file.filename
    
    try:
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse CSV
        parsed_data = csv_service.parse_book_input(str(temp_file))
        
        # Import to database
        book = csv_service.import_book_to_db(db, parsed_data)
        
        logger.info(f"Book imported: id={book.id}, title='{book.title}'")
        output_logger.info(f"IMPORT | Book '{book.title}' imported (id={book.id})")
        return book
        
    except ValueError as e:
        logger.error(f"CSV import validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to import book: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import book: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()


@router.get("/books/{book_id}", response_model=BookWithDetails)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get book details with status information"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Get additional details
    outline = db.query(Outline).filter(Outline.book_id == book_id).first()
    chapters_count = len(book.chapters) if book.chapters else 0
    
    return {
        **book.__dict__,
        "outline_status": outline.status.value if outline else None,
        "chapters_count": chapters_count,
        "final_draft_status": book.final_draft.output_status.value if book.final_draft else None
    }


@router.post("/books/{book_id}/outline/generate", response_model=OutlineResponse)
async def generate_outline(
    book_id: int,
    request: OutlineGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate or regenerate book outline"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    outline = db.query(Outline).filter(Outline.book_id == book_id).first()
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outline record not found for book {book_id}"
        )
    
    # Check if generation is allowed
    can_generate, reason = workflow_service.can_generate_outline(db, book_id)
    if not can_generate and not request.regenerate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )
    
    try:
        # Determine notes to use
        notes = outline.notes_after if outline.notes_after else outline.notes_before  # type: ignore
        
        # Generate outline
        logger.info(f"Generating outline for book {book_id}: '{book.title}'")
        outline_content = openai_service.generate_outline(
            title=book.title,
            notes_before=notes
        )
        
        # Update outline
        outline.outline_content = outline_content
        if request.regenerate:
            outline.regeneration_count += 1
        
        # Update book stage
        workflow_service.advance_book_stage(db, book_id, BookStage.OUTLINE)
        
        db.commit()
        db.refresh(outline)
        logger.info(f"Outline generated for book {book_id} ({len(outline_content)} chars)")
        output_logger.info(f"OUTLINE | Book {book_id} '{book.title}' - outline generated ({len(outline_content)} chars)")
        
        # Send notification in background
        background_tasks.add_task(
            email_service.send_outline_ready_email,
            db,
            book_id,
            book.title
        )
        
        return outline
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate outline for book {book_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate outline: {str(e)}"
        )


@router.put("/books/{book_id}/outline/notes", response_model=OutlineResponse)
def update_outline_notes(
    book_id: int,
    update: OutlineUpdate,
    db: Session = Depends(get_db)
):
    """Update outline notes and status"""
    outline = db.query(Outline).filter(Outline.book_id == book_id).first()
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outline not found for book {book_id}"
        )
    
    # Update fields
    if update.notes_after is not None:
        outline.notes_after = update.notes_after
    
    if update.status is not None:
        outline.status = update.status
    
    db.commit()
    db.refresh(outline)
    
    return outline


@router.post("/books/{book_id}/outline/regenerate", response_model=OutlineResponse)
async def regenerate_outline(
    book_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Regenerate outline using notes_after"""
    outline = db.query(Outline).filter(Outline.book_id == book_id).first()
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outline not found for book {book_id}"
        )
    
    if not outline.notes_after:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="notes_after must be provided before regenerating outline"
        )
    
    book = db.query(Book).filter(Book.id == book_id).first()
    
    try:
        # Regenerate with notes_after
        outline_content = openai_service.generate_outline(
            title=book.title,
            notes_before=outline.notes_after
        )
        
        outline.outline_content = outline_content
        outline.regeneration_count += 1
        
        db.commit()
        db.refresh(outline)
        
        # Send notification
        background_tasks.add_task(
            email_service.send_outline_ready_email,
            db,
            book_id,
            book.title
        )
        
        return outline
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate outline: {str(e)}"
        )


@router.get("/books", response_model=List[BookWithDetails])
def list_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all books"""
    books = db.query(Book).offset(skip).limit(limit).all()
    
    result = []
    for book in books:
        outline = db.query(Outline).filter(Outline.book_id == book.id).first()
        chapters_count = len(book.chapters) if book.chapters else 0
        
        result.append({
            **book.__dict__,
            "outline_status": outline.status.value if outline else None,
            "chapters_count": chapters_count,
            "final_draft_status": book.final_draft.output_status.value if book.final_draft else None
        })
    
    return result
