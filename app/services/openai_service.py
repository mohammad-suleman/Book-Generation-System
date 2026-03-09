"""
OpenAI service for AI-powered content generation
"""
import asyncio
from typing import Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.constants import (
    MAX_TOKENS_OUTLINE,
    MAX_TOKENS_CHAPTER,
    MAX_TOKENS_SUMMARY,
    TEMPERATURE
)
from app.core.logging_config import get_logger

logger = get_logger("app.services.openai")


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate_outline(self, title: str, notes_before: Optional[str] = None) -> str:
        """
        Generate a book outline based on title and notes.
        
        Args:
            title: The book title
            notes_before: Optional notes to guide outline generation
        
        Returns:
            Generated outline as a string
        """
        system_prompt = """You are an expert book outliner. Create a detailed, well-structured book outline.
The outline should include:
- A clear chapter-by-chapter breakdown
- Brief description of what each chapter will cover
- Logical flow and progression of ideas
- Accurate and informative content based on established knowledge

Format the outline clearly with chapter numbers and titles."""
        
        user_message = f"Create a detailed outline for a book titled: '{title}'"
        
        if notes_before:
            user_message += f"\n\nAdditional requirements and context:\n{notes_before}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=MAX_TOKENS_OUTLINE,
            temperature=TEMPERATURE
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned empty response")
        logger.info(f"Outline generated for '{title}' ({len(content)} chars)")
        return content.strip()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate_chapter(
        self,
        chapter_number: int,
        book_title: str,
        outline: str,
        previous_summaries: Optional[str] = None,
        chapter_notes: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Generate a book chapter with context from previous chapters.
        
        Args:
            chapter_number: The chapter number
            book_title: The book title
            outline: The full book outline
            previous_summaries: Summaries of previous chapters for context
            chapter_notes: Optional notes to guide chapter generation
        
        Returns:
            Tuple of (chapter_title, chapter_content)
        """
        system_prompt = """You are an expert book writer. Write engaging, well-researched book chapters.
Your writing should be:
- Clear and well-structured
- Factually accurate based on established knowledge
- Consistent with the book's overall outline and previous chapters
- Engaging and reader-friendly
- Well-informed with credible information

Start with the chapter title on the first line, then provide the complete chapter content."""
        
        user_message = f"""Write Chapter {chapter_number} for the book titled: '{book_title}'

Book Outline:
{outline}
"""
        
        if previous_summaries:
            user_message += f"\n\nContext from previous chapters:\n{previous_summaries}\n"
        
        user_message += f"\nWrite Chapter {chapter_number} now, maintaining continuity with previous chapters (if any)."
        
        if chapter_notes:
            user_message += f"\n\nAdditional requirements for this chapter:\n{chapter_notes}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=MAX_TOKENS_CHAPTER,
            temperature=TEMPERATURE
        )
        
        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ValueError("OpenAI returned empty response")
        content = raw_content.strip()
        
        # Extract chapter title (first line) and content
        lines = content.split('\n', 1)
        chapter_title = lines[0].strip()
        chapter_content = lines[1].strip() if len(lines) > 1 else content
        
        # Clean up chapter title
        chapter_title = chapter_title.replace('**', '').replace('#', '').strip()
        if chapter_title.lower().startswith('chapter'):
            # Remove "Chapter X:" prefix if present
            parts = chapter_title.split(':', 1)
            if len(parts) > 1:
                chapter_title = parts[1].strip()
        
        return chapter_title, chapter_content
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate_summary(self, chapter_content: str, chapter_title: str) -> str:
        """
        Generate a concise summary of a chapter for context chaining.
        
        Args:
            chapter_content: The full chapter content
            chapter_title: The chapter title
        
        Returns:
            Concise summary of the chapter
        """
        system_prompt = """You are an expert at creating concise chapter summaries.
Create a brief summary that captures the key points and main ideas of the chapter.
The summary should be 2-4 paragraphs maximum and help maintain context for writing subsequent chapters."""
        
        user_message = f"""Summarize the following chapter:

Title: {chapter_title}

Content:
{chapter_content}
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=MAX_TOKENS_SUMMARY,
            temperature=TEMPERATURE
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned empty response")
        return content.strip()


# Global service instance
openai_service = OpenAIService()
