"""
API endpoints for final draft compilation and management
"""
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false, reportOperatorIssue=false, reportOptionalMemberAccess=false
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.core.constants import BookStage, NotesStatus, OutputStatus
from app.models import Book, FinalDraft, NotificationLog
from app.schemas import FinalDraftResponse, FinalDraftUpdate, CompileRequest
from app.services.workflow_service import workflow_service
from app.services.document_service import document_service
from app.services.email_service import email_service
from app.core.logging_config import get_logger

logger = get_logger("app.api.final_draft")
output_logger = get_logger("app.output")

router = APIRouter()


@router.post("/books/{book_id}/compile", response_model=FinalDraftResponse)
async def compile_book(
    book_id: int,
    request: CompileRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Compile all chapters into final .docx document"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Check if compilation is allowed
    if not request.force:
        can_compile, reason = workflow_service.can_compile_final(db, book_id)
        if not can_compile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )
    
    try:
        # Compile document
        logger.info(f"Compiling final draft for book {book_id}: '{book.title}'")
        file_path = document_service.compile_book_to_docx(db, book_id)
        
        # Create or update final draft record
        final_draft = db.query(FinalDraft).filter(FinalDraft.book_id == book_id).first()
        
        if final_draft:
            final_draft.file_path = file_path
            final_draft.output_status = OutputStatus.COMPLETED
        else:
            final_draft = FinalDraft(
                book_id=book_id,
                review_notes_status=NotesStatus.NO_NOTES_NEEDED,
                output_status=OutputStatus.COMPLETED,
                file_path=file_path
            )
            db.add(final_draft)
        
        # Update book stage
        workflow_service.advance_book_stage(db, book_id, BookStage.COMPLETED)
        
        db.commit()
        db.refresh(final_draft)
        
        # Send notification in background
        background_tasks.add_task(
            email_service.send_final_draft_ready_email,
            db,
            book_id,
            book.title,
            file_path
        )
        
        logger.info(f"Final draft compiled for book {book_id}: {file_path}")
        output_logger.info(f"COMPILE | Book {book_id} '{book.title}' - final draft compiled: {file_path}")
        return final_draft
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to compile book {book_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile book: {str(e)}"
        )


@router.get("/books/{book_id}/final-draft", response_model=FinalDraftResponse)
def get_final_draft(book_id: int, db: Session = Depends(get_db)):
    """Get final draft details"""
    final_draft = db.query(FinalDraft).filter(FinalDraft.book_id == book_id).first()
    
    if not final_draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Final draft not found for book {book_id}"
        )
    
    return final_draft


@router.put("/books/{book_id}/final-draft/review", response_model=FinalDraftResponse)
def update_final_draft_review(
    book_id: int,
    update: FinalDraftUpdate,
    db: Session = Depends(get_db)
):
    """Update final draft review notes and status"""
    final_draft = db.query(FinalDraft).filter(FinalDraft.book_id == book_id).first()
    
    if not final_draft:
        # Create if doesn't exist
        final_draft = FinalDraft(
            book_id=book_id,
            review_notes_status=NotesStatus.NO,
            output_status=OutputStatus.READY
        )
        db.add(final_draft)
    
    # Update fields
    if update.review_notes_status is not None:
        final_draft.review_notes_status = update.review_notes_status
    
    if update.final_notes is not None:
        final_draft.final_notes = update.final_notes
    
    db.commit()
    db.refresh(final_draft)
    
    return final_draft


@router.get("/books/{book_id}/final-draft/download")
def download_final_draft(book_id: int, format: str = "docx", db: Session = Depends(get_db)):
    """Download the compiled book in docx, pdf, or txt format"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )

    allowed_formats = {"docx", "pdf", "txt"}
    if format not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Allowed: {', '.join(allowed_formats)}"
        )

    logger.info(f"Download requested for book {book_id} in format: {format}")

    if format == "docx":
        # Use existing compiled docx
        final_draft = db.query(FinalDraft).filter(FinalDraft.book_id == book_id).first()
        if not final_draft or not final_draft.file_path:  # type: ignore
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Final draft has not been compiled yet"
            )
        file_path = Path(final_draft.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compiled file not found on disk"
            )
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    try:
        if format == "pdf":
            file_path_str = document_service.compile_book_to_pdf(db, book_id)
            return FileResponse(
                path=file_path_str,
                filename=Path(file_path_str).name,
                media_type="application/pdf"
            )
        else:  # txt
            file_path_str = document_service.compile_book_to_txt(db, book_id)
            return FileResponse(
                path=file_path_str,
                filename=Path(file_path_str).name,
                media_type="text/plain"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/books/{book_id}/status")
def get_book_status(book_id: int, db: Session = Depends(get_db)):
    """Get detailed status of book generation process"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Get gating status for each stage
    can_gen_outline, outline_reason = workflow_service.can_generate_outline(db, book_id)
    can_proceed_outline, proceed_reason = workflow_service.can_proceed_from_outline(db, book_id)
    can_compile, compile_reason = workflow_service.can_compile_final(db, book_id)
    
    return {
        "book_id": book.id,
        "title": book.title,
        "current_stage": book.current_stage.value,
        "outline_status": {
            "can_generate": can_gen_outline,
            "reason": outline_reason,
            "can_proceed_to_chapters": can_proceed_outline,
            "proceed_reason": proceed_reason
        },
        "chapters": {
            "count": len(book.chapters) if book.chapters else 0,
            "chapters": [
                {
                    "number": ch.chapter_number,
                    "title": ch.title,
                    "status": ch.notes_status.value
                }
                for ch in sorted(book.chapters, key=lambda x: x.chapter_number)
            ] if book.chapters else []
        },
        "final_draft": {
            "can_compile": can_compile,
            "reason": compile_reason,
            "status": book.final_draft.output_status.value if book.final_draft else None,
            "file_ready": bool(book.final_draft and book.final_draft.file_path) if book.final_draft else False
        }
    }


@router.get("/books/{book_id}/notifications")
def get_notifications(book_id: int, db: Session = Depends(get_db)):
    """Get notification history for a book"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    notifications = db.query(NotificationLog).filter(
        NotificationLog.book_id == book_id
    ).order_by(NotificationLog.sent_at.desc()).all()
    
    return {
        "book_id": book_id,
        "notifications": [
            {
                "event_type": n.event_type.value,
                "recipient": n.recipient,
                "sent_at": n.sent_at,
                "status": n.status,
                "error_message": n.error_message
            }
            for n in notifications
        ]
    }
