"""
Handlers package for Telegram bot.

This package provides:
- Message handlers for group chat messages
- Command handlers for bot commands (/summarize, /start, etc.)
- Callback handlers for inline buttons
"""

from handlers.message_handler import (
    handle_group_message,
    setup_message_handlers,
)
from handlers.command_handler import (
    handle_start,
    handle_help,
    handle_summarize,
    setup_command_handlers,
)

__all__ = [
    # Message handlers
    "handle_group_message",
    "setup_message_handlers",
    # Command handlers
    "handle_start",
    "handle_help",
    "handle_summarize",
    "setup_command_handlers",
]
