"""
Book model - Main book entity
"""
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.core.constants import BookStage


class Book(Base):
    """Book entity"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    current_stage = Column(Enum(BookStage), default=BookStage.INPUT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    outline = relationship("Outline", back_populates="book", uselist=False, cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan", order_by="Chapter.chapter_number")
    final_draft = relationship("FinalDraft", back_populates="book", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', stage='{self.current_stage}')>"
