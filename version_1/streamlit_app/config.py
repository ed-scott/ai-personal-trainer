"""
Configuration Module for Streamlit App
=======================================

Environment and configuration management for the AI Personal Trainer app.
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class SnowflakeConfig:
    """Snowflake connection configuration."""
    account: str
    user: str
    password: str
    role: str = "TRAINING_APP_ROLE"
    warehouse: str = "TRAINING_WH"
    database: str = "TRAINING_DB"
    schema: str = "PUBLIC"
    
    @classmethod
    def from_env(cls) -> 'SnowflakeConfig':
        """Load configuration from environment variables."""
        return cls(
            account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
            user=os.getenv("SNOWFLAKE_USER", ""),
            password=os.getenv("SNOWFLAKE_PASSWORD", ""),
            role=os.getenv("SNOWFLAKE_ROLE", "TRAINING_APP_ROLE"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "TRAINING_WH"),
            database=os.getenv("SNOWFLAKE_DATABASE", "TRAINING_DB"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        )

@dataclass
class AppConfig:
    """Application configuration."""
    debug: bool = False
    log_level: str = "INFO"
    cache_ttl: int = 3600  # seconds
    max_upload_size: int = 100 * 1024 * 1024  # 100 MB
    snowflake: SnowflakeConfig = None
    
    def __post_init__(self):
        if self.snowflake is None:
            self.snowflake = SnowflakeConfig.from_env()

# Global configuration instance
config = AppConfig(
    debug=os.getenv("DEBUG", "False").lower() == "true",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)

# AI Configuration
AI_CONFIG = {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "api_key": os.getenv("OPENAI_API_KEY", ""),
}

# App features
FEATURES = {
    "weighin_tracking": True,
    "workout_logging": True,
    "running_tracking": True,
    "nutrition_logging": True,
    "ai_suggestions": True,
    "progress_charts": True,
    "data_export": True,
}
