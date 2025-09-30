"""
Message Summarizer Service.

This module handles the logic for:
- Collecting messages from MongoDB
- Generating summaries using Claude AI
- Managing message buffers
- Saving summaries to database
- Managing user summary limits
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from beanie.operators import In

from database.models import Message, Summary, MessageBuffer, User
from services.ai_service import ClaudeAIService
from config import settings

logger = logging.getLogger(__name__)


class MessageSummarizer:
    """
    Service for summarizing messages from group chats.
    
    Handles:
    - Message collection from rolling buffer
    - Summary generation
    - Summary storage with user limits
    - Buffer management
    """
    
    def __init__(self):
        """Initialize the summarizer with AI service."""
        self.ai_service = ClaudeAIService()
        logger.info("Message Summarizer initialized")
    
    async def summarize_chat(
        self,
        chat_id: int,
        user_telegram_id: int,
        message_count: Optional[int] = None,
        summary_type: str = "standard",
        language: str = "he",
        chat_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a summary of messages from a chat.
        
        Args:
            chat_id: Telegram chat ID
            user_telegram_id: User who requested the summary
            message_count: Number of messages to summarize (None = use buffer)
            summary_type: Type of summary (standard, quick, detailed, decisions, questions)
            language: Language for summary (he, en)
            chat_title: Optional chat title
            
        Returns:
            Dict with:
                - success: bool
                - summary_text: str (if success)
                - summary_id: str (if success)
                - message_count: int
                - error: str (if not success)
        """
        try:
            # Get messages to summarize
            messages = await self._get_messages_for_summary(
                chat_id=chat_id,
                message_count=message_count,
            )
            
            if not messages:
                return {
                    "success": False,
                    "error": "לא נמצאו הודעות לסיכום" if language == "he" else "No messages to summarize",
                    "message_count": 0,
                }
            
            logger.info(f"Summarizing {len(messages)} messages from chat {chat_id}")
            
            # Extract message texts
            message_texts = [msg.text for msg in messages]
            
            # Generate summary using AI
            summary_text = await self.ai_service.generate_summary(
                messages=message_texts,
                summary_type=summary_type,
                language=language,
            )
            
            # Save summary to database
            summary = Summary(
                user_telegram_id=user_telegram_id,
                chat_id=chat_id,
                summary_text=summary_text,
                message_count=len(messages),
                chat_title=chat_title,
                summary_type=summary_type,
                language=language,
                is_saved=True,
                created_at=datetime.utcnow(),
            )
            await summary.insert()
            
            # Manage user summary limit (keep only last N summaries)
            await self._manage_user_summary_limit(user_telegram_id)
            
            # Update message buffer
            await self._update_buffer_after_summary(chat_id)
            
            logger.info(
                f"Summary created successfully: {summary.id} "
                f"({len(messages)} messages, type: {summary_type})"
            )
            
            return {
                "success": True,
                "summary_text": summary_text,
                "summary_id": str(summary.id),
                "message_count": len(messages),
            }
            
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_count": 0,
            }
    
    async def _get_messages_for_summary(
        self,
        chat_id: int,
        message_count: Optional[int] = None,
    ) -> List[Message]:
        """
        Get messages to summarize from database.
        
        Args:
            chat_id: Chat ID to get messages from
            message_count: Number of messages to get (None = use buffer)
            
        Returns:
            List[Message]: Messages sorted by timestamp
        """
        if message_count:
            # Get specific number of latest messages
            messages = await Message.find(
                Message.chat_id == chat_id
            ).sort(-Message.timestamp).limit(message_count).to_list()
            
            # Reverse to get chronological order
            messages.reverse()
            
        else:
            # Get messages from buffer
            buffer = await MessageBuffer.find_one(MessageBuffer.chat_id == chat_id)
            
            if not buffer or not buffer.message_ids:
                # No buffer - get default number of messages
                messages = await Message.find(
                    Message.chat_id == chat_id
                ).sort(-Message.timestamp).limit(settings.default_summary_count).to_list()
                
                messages.reverse()
            else:
                # Get messages by IDs from buffer
                messages = await Message.find(
                    In(Message.message_id, buffer.message_ids),
                    Message.chat_id == chat_id
                ).sort(Message.timestamp).to_list()
        
        return messages
    
    async def _manage_user_summary_limit(self, user_telegram_id: int) -> None:
        """
        Keep only the last N summaries per user.
        
        Args:
            user_telegram_id: User's Telegram ID
        """
        # Get all summaries for this user, sorted by creation date
        summaries = await Summary.find(
            Summary.user_telegram_id == user_telegram_id
        ).sort(-Summary.created_at).to_list()
        
        # If more than max limit, delete old ones
        if len(summaries) > settings.max_summaries_per_user:
            old_summaries = summaries[settings.max_summaries_per_user:]
            
            for summary in old_summaries:
                await summary.delete()
                logger.debug(f"Deleted old summary {summary.id} for user {user_telegram_id}")
            
            logger.info(
                f"Cleaned up {len(old_summaries)} old summaries for user {user_telegram_id}"
            )
    
    async def _update_buffer_after_summary(self, chat_id: int) -> None:
        """
        Update message buffer after creating a summary.
        
        Args:
            chat_id: Chat ID
        """
        buffer = await MessageBuffer.find_one(MessageBuffer.chat_id == chat_id)
        
        if buffer:
            await buffer.clear_buffer()
            logger.debug(f"Cleared message buffer for chat {chat_id}")
    
    async def add_message_to_buffer(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        from_user_id: Optional[int] = None,
        from_username: Optional[str] = None,
        from_first_name: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to the rolling buffer.
        
        Args:
            chat_id: Chat ID
            message_id: Telegram message ID
            text: Message text
            from_user_id: User who sent the message
            from_username: Username
            from_first_name: First name
            reply_to_message_id: ID of message being replied to
            
        Returns:
            Dict with buffer status
        """
        try:
            # Save message to database
            message = Message(
                message_id=message_id,
                chat_id=chat_id,
                text=text,
                from_user_id=from_user_id,
                from_username=from_username,
                from_first_name=from_first_name,
                reply_to_message_id=reply_to_message_id,
                timestamp=datetime.utcnow(),
            )
            await message.insert()
            
            # Get or create buffer
            buffer = await MessageBuffer.find_one(MessageBuffer.chat_id == chat_id)
            
            if not buffer:
                buffer = MessageBuffer(
                    chat_id=chat_id,
                    buffer_size=settings.max_message_buffer,
                )
            
            # Add message to buffer
            await buffer.add_message(message_id)
            
            logger.debug(
                f"Added message {message_id} to buffer for chat {chat_id} "
                f"(buffer: {len(buffer.message_ids)}/{buffer.buffer_size})"
            )
            
            return {
                "success": True,
                "buffer_count": len(buffer.message_ids),
                "buffer_size": buffer.buffer_size,
                "should_auto_summarize": (
                    buffer.message_count_since_last_summary >= buffer.buffer_size
                ),
            }
            
        except Exception as e:
            logger.error(f"Error adding message to buffer: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_user_summaries(
        self,
        user_telegram_id: int,
        limit: int = 5,
    ) -> List[Summary]:
        """
        Get saved summaries for a user.
        
        Args:
            user_telegram_id: User's Telegram ID
            limit: Maximum number of summaries to return
            
        Returns:
            List[Summary]: User's summaries, newest first
        """
        summaries = await Summary.find(
            Summary.user_telegram_id == user_telegram_id
        ).sort(-Summary.created_at).limit(limit).to_list()
        
        return summaries
    
    async def search_summaries(
        self,
        user_telegram_id: int,
        search_term: str,
    ) -> List[Summary]:
        """
        Search summaries by text content.
        
        Args:
            user_telegram_id: User's Telegram ID
            search_term: Term to search for
            
        Returns:
            List[Summary]: Matching summaries
        """
        # MongoDB text search would require text index
        # For now, we'll do simple filtering in Python
        all_summaries = await Summary.find(
            Summary.user_telegram_id == user_telegram_id
        ).sort(-Summary.created_at).to_list()
        
        # Filter by search term (case-insensitive)
        search_lower = search_term.lower()
        matching = [
            s for s in all_summaries
            if search_lower in s.summary_text.lower()
            or (s.chat_title and search_lower in s.chat_title.lower())
        ]
        
        return matching
    
    async def get_buffer_status(self, chat_id: int) -> Dict[str, Any]:
        """
        Get current buffer status for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Dict with buffer information
        """
        buffer = await MessageBuffer.find_one(MessageBuffer.chat_id == chat_id)
        
        if not buffer:
            return {
                "exists": False,
                "message_count": 0,
                "buffer_size": settings.max_message_buffer,
            }
        
        return {
            "exists": True,
            "message_count": len(buffer.message_ids),
            "buffer_size": buffer.buffer_size,
            "messages_since_last_summary": buffer.message_count_since_last_summary,
            "last_summary_at": buffer.last_summary_at,
        }
