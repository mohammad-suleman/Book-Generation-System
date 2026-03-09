"""
CSV service for importing book data from CSV files
"""
import pandas as pd
from sqlalchemy.orm import Session
from typing import Dict, Optional
from pathlib import Path

from app.models import Book, Outline
from app.core.constants import NotesStatus


class CSVService:
    """Service for handling CSV import and parsing"""
    
    def parse_book_input(self, csv_file_path: str) -> Dict:
        """
        Parse book input from CSV file.
        
        Expected CSV columns:
        - title (required)
        - notes_on_outline_before (required)
        - notes_on_outline_after (optional)
        - status_outline_notes (optional, default: 'no')
        - chapter_notes_status (optional)
        - chapter_notes (optional)
        - final_review_notes_status (optional)
        
        Args:
            csv_file_path: Path to CSV file
        
        Returns:
            Dictionary with parsed book data
        
        Raises:
            ValueError: If required fields are missing or file is invalid
        """
        if not Path(csv_file_path).exists():
            raise ValueError(f"CSV file not found: {csv_file_path}")
        
        # Read CSV
        try:
            df = pd.read_csv(csv_file_path)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        # Get first row (single book per CSV)
        row = df.iloc[0]
        
        # Validate required fields
        if 'title' not in df.columns or pd.isna(row.get('title')):
            raise ValueError("'title' column is required and cannot be empty")
        
        if 'notes_on_outline_before' not in df.columns:
            raise ValueError("'notes_on_outline_before' column is required")
        
        # Parse data
        parsed_data = {
            'title': str(row['title']).strip(),
            'notes_on_outline_before': str(row.get('notes_on_outline_before', '')).strip() if not pd.isna(row.get('notes_on_outline_before')) else None,
            'notes_on_outline_after': str(row.get('notes_on_outline_after', '')).strip() if not pd.isna(row.get('notes_on_outline_after')) else None,
            'status_outline_notes': self._parse_status(row.get('status_outline_notes', 'no')),
            'chapter_notes_status': self._parse_status(row.get('chapter_notes_status', 'no')),
            'chapter_notes': str(row.get('chapter_notes', '')).strip() if not pd.isna(row.get('chapter_notes')) else None,
            'final_review_notes_status': self._parse_status(row.get('final_review_notes_status', 'no'))
        }
        
        return parsed_data
    
    def _parse_status(self, status_value) -> NotesStatus:
        """
        Parse status value from CSV to NotesStatus enum.
        
        Args:
            status_value: Status value from CSV
        
        Returns:
            NotesStatus enum value
        """
        if pd.isna(status_value):
            return NotesStatus.NO
        
        status_str = str(status_value).strip().lower()
        
        if status_str in ['yes', 'y', 'true', '1']:
            return NotesStatus.YES
        elif status_str in ['no_notes_needed', 'no notes needed', 'proceed', 'continue']:
            return NotesStatus.NO_NOTES_NEEDED
        else:
            return NotesStatus.NO
    
    def import_book_to_db(self, db: Session, parsed_data: Dict) -> Book:
        """
        Create book and outline records in database from parsed data.
        
        Args:
            db: Database session
            parsed_data: Parsed book data from CSV
        
        Returns:
            Created Book object
        """
        # Create book record
        book = Book(
            title=parsed_data['title'],
            current_stage='input'
        )
        db.add(book)
        db.flush()  # Get book ID
        
        # Create outline record
        outline = Outline(
            book_id=book.id,
            notes_before=parsed_data['notes_on_outline_before'],
            notes_after=parsed_data.get('notes_on_outline_after'),
            status=parsed_data.get('status_outline_notes', NotesStatus.NO)
        )
        db.add(outline)
        
        db.commit()
        db.refresh(book)
        
        return book


# Global service instance
csv_service = CSVService()
