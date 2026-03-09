"""
NotificationLog model - Email notification tracking
"""
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.core.constants import NotificationEvent


class NotificationLog(Base):
    """Notification log entity"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    event_type = Column(Enum(NotificationEvent), nullable=False)
    recipient = Column(String(255), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="sent", nullable=False)  # sent, failed
    error_message = Column(String(500), nullable=True)
    
    # Relationships
    book = relationship("Book", back_populates="notifications")
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, book_id={self.book_id}, event='{self.event_type}')>"
