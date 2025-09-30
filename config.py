"""
Configuration management using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============== Telegram Bot ==============
    telegram_bot_token: str = Field(
        ...,
        description="Telegram Bot API token from @BotFather"
    )
    
    # ============== MongoDB ==============
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL"
    )
    mongodb_db_name: str = Field(
        default="telegram_summarizer",
        description="MongoDB database name"
    )
    
    # ============== Claude AI ==============
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic API key for Claude"
    )
    claude_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude model to use for summaries"
    )
    claude_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens for Claude responses"
    )
    claude_timeout: int = Field(
        default=120,
        description="Timeout for Claude API calls (seconds)"
    )
    
    # ============== Bot Behavior ==============
    max_message_buffer: int = Field(
        default=50,
        description="Number of messages to keep in buffer"
    )
    max_summaries_per_user: int = Field(
        default=5,
        description="Maximum summaries to keep per user in private chat"
    )
    default_summary_count: int = Field(
        default=50,
        description="Default number of messages to summarize"
    )
    
    # ============== Application ==============
    app_env: str = Field(
        default="development",
        description="Application environment: development, staging, production"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    # ============== Optional: Render Deployment ==============
    render_external_url: Optional[str] = Field(
        default=None,
        description="Render external URL for webhooks (if deployed on Render)"
    )
    port: int = Field(
        default=8080,
        description="Port for webhook server"
    )
    
    @field_validator("telegram_bot_token")
    @classmethod
    def validate_telegram_token(cls, v: str) -> str:
        """Validate Telegram bot token format."""
        if not v or len(v) < 40:
            raise ValueError(
                "Invalid Telegram bot token. "
                "Get one from @BotFather on Telegram"
            )
        return v
    
    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        """Validate Anthropic API key format."""
        if not v or not v.startswith("sk-ant-"):
            raise ValueError(
                "Invalid Anthropic API key. "
                "Get one from https://console.anthropic.com/"
            )
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"


# Global settings instance
settings = Settings()
