"""
FinalDraft model - Final compiled book entity
"""
from sqlalchemy import Column, Integer, Text, Enum, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.core.constants import NotesStatus, OutputStatus


class FinalDraft(Base):
    """Final draft entity"""
    __tablename__ = "final_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, unique=True)
    review_notes_status = Column(Enum(NotesStatus), default=NotesStatus.NO, nullable=False)
    final_notes = Column(Text, nullable=True)
    output_status = Column(Enum(OutputStatus), default=OutputStatus.READY, nullable=False)
    file_path = Column(String(500), nullable=True)  # Path to generated .docx file
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    book = relationship("Book", back_populates="final_draft")
    
    def __repr__(self):
        return f"<FinalDraft(id={self.id}, book_id={self.book_id}, status='{self.output_status}')>"
