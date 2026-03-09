"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-5.4-2026-03-05"
    
    # MySQL Database Configuration
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str
    mysql_database: str = "book_generation_db"
    
    # SMTP Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    notification_email: str
    
    # Application Configuration
    app_name: str = "Book Generation System"
    app_version: str = "1.0.0"
    debug: bool = True
    output_dir: str = "outputs"
    
    @property
    def database_url(self) -> str:
        """Construct MySQL database URL with properly encoded password"""
        # URL-encode the password to handle special characters like @
        encoded_password = quote_plus(self.mysql_password)
        return f"mysql+pymysql://{self.mysql_user}:{encoded_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"


# Global settings instance
settings = Settings()  # type: ignore  # Pydantic will load from .env
