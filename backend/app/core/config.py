from functools import lru_cache
from pathlib import Path
from typing import Optional
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "Predictive Maintenance Platform"
    environment: str = "local"
    debug: bool = True

    # Database
    postgres_user: str = "pm_user"
    postgres_password: str = "pm_pass"
    postgres_db: str = "pm_db"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # AI service
    ai_service_url: str = "http://ai-service:8000"

    # Auth / Security
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60

    # Notifications
    email_smtp_host: str = "smtp.gmail.com" # Assuming Gmail/GSuite for now or standard
    email_smtp_port: int = 587
    email_smtp_user: str = "tanirajsingh@itx-solution.com"
    email_smtp_pass: str = "tanirajsingh1122"
    slack_webhook_url: Optional[str] = None
    notification_email: str = "tanirajsingh574@gmail.com"

    # Reporting
    reports_dir: Path = Path("./reports")
    
    # Refresh token
    refresh_token_exp_days: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Environment variables take precedence over env_file
        env_file_ignore_empty = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    return settings

def clear_settings_cache():
    """Clear settings cache - useful for testing or env var changes"""
    get_settings.cache_clear()

