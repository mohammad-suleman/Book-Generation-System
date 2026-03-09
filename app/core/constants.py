"""
Application constants and enums
"""
from enum import Enum


class BookStage(str, Enum):
    """Book generation stages"""
    INPUT = "input"
    OUTLINE = "outline"
    CHAPTERS = "chapters"
    COMPILATION = "compilation"
    COMPLETED = "completed"


class NotesStatus(str, Enum):
    """Status for notes review"""
    YES = "yes"  # Waiting for notes
    NO = "no"  # No notes provided, paused
    NO_NOTES_NEEDED = "no_notes_needed"  # Proceed without notes


class OutputStatus(str, Enum):
    """Final draft output status"""
    READY = "ready"  # Ready to compile
    PAUSED = "paused"  # Paused due to missing input
    COMPLETED = "completed"  # Final draft compiled


class NotificationEvent(str, Enum):
    """Types of notification events"""
    OUTLINE_READY = "outline_ready"
    WAITING_FOR_OUTLINE_NOTES = "waiting_for_outline_notes"
    WAITING_FOR_CHAPTER_NOTES = "waiting_for_chapter_notes"
    CHAPTER_GENERATED = "chapter_generated"
    FINAL_DRAFT_READY = "final_draft_ready"
    ERROR = "error"
    PAUSED = "paused"


# OpenAI Configuration
# gpt-4-0125-preview supports max 4096 completion tokens
MAX_TOKENS_OUTLINE = 4000
MAX_TOKENS_CHAPTER = 4096
MAX_TOKENS_SUMMARY = 500
TEMPERATURE = 0.01
# Chapter Context Configuration
MAX_CONTEXT_CHAPTERS = 10  # Maximum number of previous chapters to include in context
