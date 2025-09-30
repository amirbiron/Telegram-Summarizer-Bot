"""
Services package for business logic.

This package provides:
- AI service for Claude API integration
- Summarizer for generating summaries from messages
- Search functionality for saved summaries
"""

from services.ai_service import ClaudeAIService
from services.summarizer import MessageSummarizer

__all__ = [
    "ClaudeAIService",
    "MessageSummarizer",
]
