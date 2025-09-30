"""
Telegram Summarizer Bot - Main Entry Point

This is the main entry point for the Telegram bot that summarizes group conversations.

Features:
- Group message tracking with rolling buffer (50 messages)
- AI-powered summaries using Claude Sonnet 4.5
- Multiple summary types (quick, detailed, decisions, questions)
- Save up to 5 summaries per user
- Search in saved summaries
- MongoDB for data persistence

Usage:
    python main.py

Environment Variables Required:
    TELEGRAM_BOT_TOKEN - Bot token from @BotFather
    ANTHROPIC_API_KEY - Claude API key
    MONGODB_URL - MongoDB connection string
    
See .env.example for all configuration options.
"""

import asyncio
import os
import logging
import sys
from telegram import Update
from telegram.ext import Application, ApplicationBuilder

from config import settings
from database import init_db, close_db
from handlers import setup_command_handlers, setup_message_handlers
from utils.logger import setup_logging
from utils.health_server import HealthServer

# Setup logging
logger = setup_logging()


async def post_init(application: Application) -> None:
    """
    Initialize bot after application is created.
    
    This function runs once when the bot starts up.
    It initializes the database connection.
    
    Args:
        application: Telegram bot application
    """
    logger.info("Starting bot initialization...")
    
    try:
        # Initialize MongoDB connection
        await init_db()
        logger.info("Database initialized successfully")
        
        # Test Claude API connection
        from services.ai_service import ClaudeAIService
        ai_service = ClaudeAIService()
        connection_ok = await ai_service.test_connection()
        
        if connection_ok:
            logger.info("Claude API connection successful")
        else:
            logger.warning("Claude API connection test failed")
        
        logger.info("✅ Bot initialization completed successfully")
        logger.info(f"Bot is ready! Environment: {settings.app_env}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}", exc_info=True)
        sys.exit(1)


async def post_shutdown(application: Application) -> None:
    """
    Clean up resources when bot is shutting down.
    
    This function runs once when the bot is stopped.
    It closes the database connection.
    
    Args:
        application: Telegram bot application
    """
    logger.info("Starting bot shutdown...")
    
    try:
        # Stop health server if running
        try:
            health_server = application.bot_data.get("health_server")
            if isinstance(health_server, HealthServer):
                health_server.stop()
        except Exception:
            pass

        # Close MongoDB connection
        await close_db()
        logger.info("Database connection closed")
        
        logger.info("✅ Bot shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


async def error_handler(update: object, context) -> None:
    """
    Handle errors that occur during bot operation.
    
    This function is called whenever an unhandled exception occurs
    in any handler.
    
    Args:
        update: Telegram update object (may be None)
        context: Bot context containing error information
    """
    logger.error(f"Exception while handling an update:", exc_info=context.error)
    
    # Try to send error message to user if possible
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ אופס! משהו השתבש.\n"
                "הבעיה נרשמה והצוות שלנו יטפל בזה בקרוב.\n\n"
                "נסה שוב או צור איתנו קשר אם הבעיה ממשיכה."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


def main() -> None:
    """
    Main function to start the bot.
    
    Creates the Telegram bot application, registers handlers,
    and starts polling for updates.
    """
    logger.info("=" * 60)
    logger.info("🤖 Telegram Summarizer Bot Starting...")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"MongoDB: {settings.mongodb_db_name}")
    logger.info(f"Claude Model: {settings.claude_model}")
    logger.info(f"Max Buffer Size: {settings.max_message_buffer}")
    logger.info(f"Max Summaries Per User: {settings.max_summaries_per_user}")
    logger.info("=" * 60)
    
    try:
        # Create application
        application = (
            ApplicationBuilder()
            .token(settings.telegram_bot_token)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )
        
        # Start lightweight HTTP health server so Render detects an open port
        port_env = os.environ.get("PORT")
        try:
            port = int(port_env) if port_env else int(settings.port)
        except Exception:
            port = int(settings.port)

        health_server = HealthServer(port=port)
        health_server.start()
        application.bot_data["health_server"] = health_server
        logger.info(f"Health server started on 0.0.0.0:{port}")

        # Register handlers
        setup_command_handlers(application)
        setup_message_handlers(application)
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        logger.info("All handlers registered successfully")
        logger.info("Starting polling...")
        logger.info("=" * 60)
        logger.info("✅ Bot is now running! Press Ctrl+C to stop.")
        logger.info("=" * 60)
        
        # Start the bot (polling mode)
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # Drop old updates on restart
        )
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    """
    Entry point when running the script directly.
    
    Run with:
        python main.py
    """
    main()
