"""
MongoDB document models using Beanie ODM.

Models follow this structure:
1. Required fields first (no default)
2. Optional/default fields after

All models inherit from Beanie's Document class.
"""

from datetime import datetime
from typing import Optional, List
from beanie import Document, Indexed
from pydantic import Field


class User(Document):
    """
    Telegram user document.
    
    Stores user information and preferences.
    """
    
    # ========== Required fields ==========
    telegram_id: Indexed(int, unique=True)  # Unique Telegram user ID
    
    # ========== Optional/Default fields ==========
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_bot: bool = False
    language_code: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: Optional[datetime] = None
    
    class Settings:
        name = "users"  # Collection name in MongoDB
        indexes = [
            "telegram_id",  # Index for fast lookups
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "username": "john_doe",
                "first_name": "John",
                "last_name": "Doe",
                "is_bot": False,
                "language_code": "en",
                "is_active": True,
            }
        }


class Message(Document):
    """
    Message document for storing group messages.
    
    Used for the rolling buffer of messages to summarize.
    """
    
    # ========== Required fields ==========
    message_id: int  # Telegram message ID
    chat_id: Indexed(int)  # Group chat ID
    text: str  # Message text content
    
    # ========== Optional/Default fields ==========
    from_user_id: Optional[int] = None  # User who sent the message
    from_username: Optional[str] = None
    from_first_name: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "messages"
        indexes = [
            "chat_id",
            "timestamp",
            [("chat_id", 1), ("timestamp", -1)],  # Compound index
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 12345,
                "chat_id": -1001234567890,
                "text": "Hello, this is a test message!",
                "from_user_id": 123456789,
                "from_username": "john_doe",
                "from_first_name": "John",
                "timestamp": "2025-09-30T10:30:00",
            }
        }


class Summary(Document):
    """
    Summary document for storing generated summaries.
    
    Keeps track of summaries sent to users.
    """
    
    # ========== Required fields ==========
    user_telegram_id: Indexed(int)  # User who requested the summary
    chat_id: int  # Group chat where summary was generated
    summary_text: str  # The actual summary content
    message_count: int  # Number of messages summarized
    
    # ========== Optional/Default fields ==========
    chat_title: Optional[str] = None
    summary_type: str = "standard"  # standard, quick, detailed, decisions, questions
    language: str = "he"  # Summary language (Hebrew by default)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_saved: bool = True  # Whether saved to user's private chat
    
    class Settings:
        name = "summaries"
        indexes = [
            "user_telegram_id",
            "created_at",
            [("user_telegram_id", 1), ("created_at", -1)],  # Compound index
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_telegram_id": 123456789,
                "chat_id": -1001234567890,
                "summary_text": "📌 סיכום השיחה:\n• נקודה 1\n• נקודה 2",
                "message_count": 50,
                "chat_title": "My Group Chat",
                "summary_type": "standard",
                "language": "he",
                "is_saved": True,
            }
        }


class MessageBuffer(Document):
    """
    Message buffer document for managing rolling window of messages per chat.
    
    This stores the current buffer state for each group chat.
    Helps manage the 50-message rolling window.
    """
    
    # ========== Required fields ==========
    chat_id: Indexed(int, unique=True)  # Unique per chat
    
    # ========== Optional/Default fields ==========
    message_ids: List[int] = Field(default_factory=list)  # List of message IDs in buffer
    buffer_size: int = 50  # Max buffer size
    last_summary_at: Optional[datetime] = None
    message_count_since_last_summary: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "message_buffers"
        indexes = [
            "chat_id",
        ]
    
    async def add_message(self, message_id: int) -> None:
        """
        Add a message to the buffer (FIFO).
        
        Args:
            message_id: Telegram message ID to add
        """
        self.message_ids.append(message_id)
        
        # Keep only the last N messages (rolling window)
        if len(self.message_ids) > self.buffer_size:
            self.message_ids = self.message_ids[-self.buffer_size:]
        
        self.message_count_since_last_summary += 1
        self.updated_at = datetime.utcnow()
        await self.save()
    
    async def clear_buffer(self) -> None:
        """Clear the message buffer after summarization."""
        self.message_ids = []
        self.message_count_since_last_summary = 0
        self.last_summary_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        await self.save()
    
    async def get_message_count(self) -> int:
        """Get current number of messages in buffer."""
        return len(self.message_ids)
    
    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": -1001234567890,
                "message_ids": [123, 124, 125, 126, 127],
                "buffer_size": 50,
                "message_count_since_last_summary": 25,
            }
        }
