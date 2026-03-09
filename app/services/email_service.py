"""
Email service for sending notifications via SMTP
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.constants import NotificationEvent
from app.models import NotificationLog
from app.core.logging_config import get_logger

logger = get_logger("app.services.email")


class EmailService:
    """Service for sending email notifications"""
    
    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        db: Optional[Session] = None,
        book_id: Optional[int] = None,
        event_type: Optional[NotificationEvent] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            recipient: Email recipient
            subject: Email subject
            body: Email body (HTML or plain text)
            db: Database session for logging
            book_id: Book ID for logging
            event_type: Event type for logging
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.smtp_from_email
            message["To"] = recipient
            
            # Add body
            part = MIMEText(body, "html" if "<html>" in body.lower() else "plain")
            message.attach(part)
            
            # Send email using SSL/TLS (port 465)
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=True
            )
            
            # Log notification
            if db and book_id and event_type:
                log = NotificationLog(
                    book_id=book_id,
                    event_type=event_type,
                    recipient=recipient,
                    status="sent"
                )
                db.add(log)
                db.commit()
            
            return True
            
        except Exception as e:
            # Log error
            if db and book_id and event_type:
                log = NotificationLog(
                    book_id=book_id,
                    event_type=event_type,
                    recipient=recipient,
                    status="failed",
                    error_message=str(e)
                )
                db.add(log)
                db.commit()
            
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False
    
    async def send_outline_ready_email(self, db: Session, book_id: int, book_title: str):
        """Send notification that outline is ready for review"""
        subject = f"Outline Ready: {book_title}"
        body = f"""
        <html>
        <body>
            <h2>Outline Ready for Review</h2>
            <p>The outline for "<strong>{book_title}</strong>" (Book ID: {book_id}) has been generated and is ready for your review.</p>
            <p>Please review the outline and provide feedback through the API:</p>
            <ul>
                <li>To approve and proceed: Set status to "no_notes_needed"</li>
                <li>To request changes: Add notes_after and set status to "yes"</li>
            </ul>
            <p>Book ID: {book_id}</p>
        </body>
        </html>
        """
        
        await self.send_email(
            recipient=settings.notification_email,
            subject=subject,
            body=body,
            db=db,
            book_id=book_id,
            event_type=NotificationEvent.OUTLINE_READY
        )
    
    async def send_waiting_for_notes_email(
        self,
        db: Session,
        book_id: int,
        book_title: str,
        stage: str,
        detail: str
    ):
        """Send notification that system is waiting for notes"""
        subject = f"Waiting for Notes: {book_title} - {stage}"
        body = f"""
        <html>
        <body>
            <h2>Waiting for Your Input</h2>
            <p>The book generation process for "<strong>{book_title}</strong>" (Book ID: {book_id}) is paused and waiting for your notes.</p>
            <p><strong>Stage:</strong> {stage}</p>
            <p><strong>Detail:</strong> {detail}</p>
            <p>Please provide your feedback through the API to continue the generation process.</p>
        </body>
        </html>
        """
        
        await self.send_email(
            recipient=settings.notification_email,
            subject=subject,
            body=body,
            db=db,
            book_id=book_id,
            event_type=NotificationEvent.WAITING_FOR_OUTLINE_NOTES
        )
    
    async def send_chapter_generated_email(
        self,
        db: Session,
        book_id: int,
        book_title: str,
        chapter_number: int
    ):
        """Send notification that a chapter has been generated"""
        subject = f"Chapter {chapter_number} Generated: {book_title}"
        body = f"""
        <html>
        <body>
            <h2>Chapter Generated</h2>
            <p>Chapter {chapter_number} for "<strong>{book_title}</strong>" (Book ID: {book_id}) has been generated.</p>
            <p>Please review the chapter and provide feedback if needed.</p>
        </body>
        </html>
        """
        
        await self.send_email(
            recipient=settings.notification_email,
            subject=subject,
            body=body,
            db=db,
            book_id=book_id,
            event_type=NotificationEvent.CHAPTER_GENERATED
        )
    
    async def send_final_draft_ready_email(
        self,
        db: Session,
        book_id: int,
        book_title: str,
        file_path: str
    ):
        """Send notification that final draft is compiled"""
        subject = f"Final Draft Ready: {book_title}"
        body = f"""
        <html>
        <body>
            <h2>Final Draft Compiled</h2>
            <p>The final draft for "<strong>{book_title}</strong>" (Book ID: {book_id}) has been successfully compiled.</p>
            <p><strong>File Location:</strong> {file_path}</p>
            <p>You can download the final document through the API.</p>
        </body>
        </html>
        """
        
        await self.send_email(
            recipient=settings.notification_email,
            subject=subject,
            body=body,
            db=db,
            book_id=book_id,
            event_type=NotificationEvent.FINAL_DRAFT_READY
        )
    
    async def send_error_notification(
        self,
        db: Session,
        book_id: int,
        book_title: str,
        error_message: str
    ):
        """Send error notification"""
        subject = f"Error: {book_title}"
        body = f"""
        <html>
        <body>
            <h2>Book Generation Error</h2>
            <p>An error occurred during the generation process for "<strong>{book_title}</strong>" (Book ID: {book_id}).</p>
            <p><strong>Error:</strong> {error_message}</p>
            <p>Please check the system logs and take appropriate action.</p>
        </body>
        </html>
        """
        
        await self.send_email(
            recipient=settings.notification_email,
            subject=subject,
            body=body,
            db=db,
            book_id=book_id,
            event_type=NotificationEvent.ERROR
        )


# Global service instance
email_service = EmailService()
