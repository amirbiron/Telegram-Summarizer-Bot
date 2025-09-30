"""
Logging configuration for the bot.

This module sets up structured logging with:
- Console output with colors
- File output (optional)
- Different log levels per environment
- Proper formatting
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import settings


# ANSI color codes for console output
class LogColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Log levels
    DEBUG = "\033[36m"      # Cyan
    INFO = "\033[32m"       # Green
    WARNING = "\033[33m"    # Yellow
    ERROR = "\033[31m"      # Red
    CRITICAL = "\033[35m"   # Magenta
    
    # Component colors
    TIMESTAMP = "\033[90m"  # Gray
    MODULE = "\033[94m"     # Light Blue


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output.
    """
    
    LEVEL_COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format
            
        Returns:
            str: Formatted log message with colors
        """
        # Get color for this log level
        level_color = self.LEVEL_COLORS.get(record.levelno, LogColors.RESET)
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        colored_timestamp = f"{LogColors.TIMESTAMP}{timestamp}{LogColors.RESET}"
        
        # Format level name
        colored_level = f"{level_color}{record.levelname:<8}{LogColors.RESET}"
        
        # Format module name
        colored_module = f"{LogColors.MODULE}{record.name:<25}{LogColors.RESET}"
        
        # Format message
        message = record.getMessage()
        
        # Handle exceptions
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        # Build final message
        return f"{colored_timestamp} | {colored_level} | {colored_module} | {message}"


class PlainFormatter(logging.Formatter):
    """
    Plain formatter without colors for file output.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record without colors.
        
        Args:
            record: Log record to format
            
        Returns:
            str: Formatted log message
        """
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        module = record.name
        message = record.getMessage()
        
        # Handle exceptions
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        return f"{timestamp} | {level:<8} | {module:<25} | {message}"


def setup_logging(
    log_file: Optional[str] = None,
    log_to_file: bool = False,
) -> logging.Logger:
    """
    Setup logging configuration for the bot.
    
    Args:
        log_file: Optional path to log file
        log_to_file: Whether to also log to a file
        
    Returns:
        logging.Logger: Configured root logger
    """
    # Get log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # === Console Handler ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use colored formatter for console
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # === File Handler (optional) ===
    if log_to_file:
        if not log_file:
            # Create logs directory if it doesn't exist
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            # Generate log file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / f"bot_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Use plain formatter for file
        file_handler.setFormatter(PlainFormatter())
        root_logger.addHandler(file_handler)
    
    # === Configure third-party loggers ===
    
    # Reduce noise from httpx/httpcore
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Reduce noise from telegram library
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext").setLevel(logging.WARNING)
    
    # Reduce noise from motor/pymongo
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    
    # Log initial message
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log level: {settings.log_level}")
    if log_to_file:
        root_logger.info(f"Logging to file: {log_file}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
