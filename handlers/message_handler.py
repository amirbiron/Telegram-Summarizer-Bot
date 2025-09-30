"""
Message Handler for Telegram group messages.

Handles:
- All messages in group chats
- Adding messages to rolling buffer
- User tracking and updates
- Auto-summary triggers
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, Application

from database.models import User
from services.summarizer import MessageSummarizer
from config import settings

logger = logging.getLogger(__name__)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming messages in group chats.
    
    This handler:
    1. Saves the message to the rolling buffer
    2. Updates user information
    3. Checks if auto-summary should trigger
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    message = update.message
    
    # Skip if no message or no text
    if not message or not message.text:
        return
    
    # Skip bot commands (handled separately)
    if message.text.startswith('/'):
        return
    
    # Get chat and user info
    chat = message.chat
    user = message.from_user
    
    # Only process group/supergroup messages
    if chat.type not in ['group', 'supergroup']:
        return
    
    try:
        # Update user in database
        await _update_user(user)
        
        # Add message to buffer
        summarizer = MessageSummarizer()
        buffer_status = await summarizer.add_message_to_buffer(
            chat_id=chat.id,
            message_id=message.message_id,
            text=message.text,
            from_user_id=user.id,
            from_username=user.username,
            from_first_name=user.first_name,
            reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
        )
        
        if not buffer_status["success"]:
            logger.error(f"Failed to add message to buffer: {buffer_status.get('error')}")
            return
        
        logger.debug(
            f"Message {message.message_id} added to buffer for chat {chat.id} "
            f"({buffer_status['buffer_count']}/{buffer_status['buffer_size']})"
        )
        
        # Check if auto-summary should trigger (50 new messages since last summary)
        if buffer_status.get("should_auto_summarize", False):
            logger.info(
                f"Auto-summary triggered for chat {chat.id} "
                f"({buffer_status['buffer_count']} messages in buffer)"
            )
            # Note: Auto-summary is optional feature
            # For now, we just log it. Can be implemented later.
            # await _trigger_auto_summary(chat, context)
        
    except Exception as e:
        logger.error(f"Error handling group message: {e}", exc_info=True)


async def _update_user(user) -> User:
    """
    Update or create user in database.
    
    Args:
        user: Telegram user object
        
    Returns:
        User: Updated/created user document
    """
    try:
        # Find existing user
        db_user = await User.find_one(User.telegram_id == user.id)
        
        if db_user:
            # Update existing user
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.language_code = user.language_code
            db_user.is_bot = user.is_bot
            db_user.last_interaction = datetime.utcnow()
            db_user.updated_at = datetime.utcnow()
            await db_user.save()
        else:
            # Create new user
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
                is_bot=user.is_bot,
                last_interaction=datetime.utcnow(),
            )
            await db_user.insert()
            logger.info(f"New user registered: {user.id} (@{user.username})")
        
        return db_user
        
    except Exception as e:
        logger.error(f"Error updating user {user.id}: {e}")
        raise


async def _trigger_auto_summary(chat, context: ContextTypes.DEFAULT_TYPE):
    """
    Trigger automatic summary after 50 messages.
    
    This is an optional feature that can be enabled.
    
    Args:
        chat: Telegram chat object
        context: Bot context
    """
    try:
        summarizer = MessageSummarizer()
        
        # Create summary
        result = await summarizer.summarize_chat(
            chat_id=chat.id,
            user_telegram_id=context.bot.id,  # Bot's own ID for auto-summaries
            message_count=None,  # Use buffer
            summary_type="standard",
            language="he",
            chat_title=chat.title,
        )
        
        if result["success"]:
            # Send summary to group
            summary_message = (
                f"📌 סיכום אוטומטי ({result['message_count']} הודעות):\n\n"
                f"{result['summary_text']}\n\n"
                f"💡 לחץ על הכפתור למטה לשמירת הסיכום בצ'אט הפרטי איתי"
            )
            
            await context.bot.send_message(
                chat_id=chat.id,
                text=summary_message,
                parse_mode='HTML',
            )
            
            logger.info(f"Auto-summary sent to chat {chat.id}")
        else:
            logger.error(f"Failed to create auto-summary: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in auto-summary: {e}", exc_info=True)


def setup_message_handlers(application: Application):
    """
    Register message handlers with the application.
    
    Args:
        application: Telegram bot application
    """
    # Handle all text messages in groups (excluding commands)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP),
            handle_group_message
        )
    )
    
    logger.info("Message handlers registered")
