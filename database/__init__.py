"""
Database package for MongoDB with Beanie ODM.

This package provides:
- MongoDB connection management
- Beanie document models (User, Message, Summary)
- Database initialization utilities
"""

from database.db import init_db, close_db, get_db
from database.models import User, Message, Summary, MessageBuffer

__all__ = [
    # Connection
    "init_db",
    "close_db",
    "get_db",
    # Models
    "User",
    "Message",
    "Summary",
    "MessageBuffer",
]
