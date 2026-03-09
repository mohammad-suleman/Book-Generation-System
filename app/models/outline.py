"""
Outline model - Book outline entity
"""
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.core.constants import NotesStatus


class Outline(Base):
    """Outline entity"""
    __tablename__ = "outlines"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, unique=True)
    notes_before = Column(Text, nullable=True)  # Notes before generating outline
    outline_content = Column(Text, nullable=True)  # Generated outline
    notes_after = Column(Text, nullable=True)  # Notes after reviewing outline
    status = Column(Enum(NotesStatus), default=NotesStatus.NO, nullable=False)
    regeneration_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    book = relationship("Book", back_populates="outline")
    
    def __repr__(self):
        return f"<Outline(id={self.id}, book_id={self.book_id}, status='{self.status}')>"
