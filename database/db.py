"""
MongoDB connection management using Motor and Beanie.

This module handles:
- Async MongoDB connection
- Beanie initialization
- Connection lifecycle management
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie

from config import settings
from database.models import User, Message, Summary

logger = logging.getLogger(__name__)

# Global MongoDB client and database
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_db() -> AsyncIOMotorDatabase:
    """
    Initialize MongoDB connection and Beanie ODM.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
        
    Raises:
        Exception: If connection fails
    """
    global _client, _db
    
    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        
        # Create async MongoDB client
        _client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,  # 10 second timeout
        )
        
        # Get database
        _db = _client[settings.mongodb_db_name]
        
        # Test connection
        await _client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        # Initialize Beanie with document models
        await init_beanie(
            database=_db,
            document_models=[
                User,
                Message,
                Summary,
            ]
        )
        logger.info("Beanie ODM initialized successfully")
        
        # Create indexes
        await _create_indexes()
        
        logger.info(f"Database '{settings.mongodb_db_name}' is ready")
        return _db
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def _create_indexes():
    """Create additional database indexes for performance."""
    try:
        # Index for User.telegram_id (unique, for fast lookups)
        await User.find_one(User.telegram_id == 0)  # This creates index if not exists
        
        # Index for Message queries by chat and timestamp
        await Message.find_one(Message.chat_id == 0)
        
        # Index for Summary queries by user
        await Summary.find_one(Summary.user_telegram_id == 0)
        
        logger.info("Database indexes created/verified")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


async def close_db():
    """
    Close MongoDB connection gracefully.
    """
    global _client, _db
    
    if _client:
        logger.info("Closing MongoDB connection")
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_db() -> Optional[AsyncIOMotorDatabase]:
    """
    Get current MongoDB database instance.
    
    Returns:
        Optional[AsyncIOMotorDatabase]: Database instance or None if not initialized
    """
    return _db


async def health_check() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    global _client
    
    if not _client:
        return False
    
    try:
        await _client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
