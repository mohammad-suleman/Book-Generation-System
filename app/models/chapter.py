"""
Chapter model - Book chapter entity
"""
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.core.constants import NotesStatus


class Chapter(Base):
    """Chapter entity"""
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint('book_id', 'chapter_number', name='uix_book_chapter'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)  # Summary for context chaining
    notes = Column(Text, nullable=True)  # Editor notes for regeneration
    notes_status = Column(Enum(NotesStatus), default=NotesStatus.NO, nullable=False)
    regeneration_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    book = relationship("Book", back_populates="chapters")
    
    def __repr__(self):
        return f"<Chapter(id={self.id}, book_id={self.book_id}, number={self.chapter_number}, status='{self.notes_status}')>"
