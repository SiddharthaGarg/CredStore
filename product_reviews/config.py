"""Configuration settings for the product reviews module."""

import os
from typing import Optional

# Try to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings:
    """Application settings."""
    
    def __init__(self):
        # PostgreSQL settings
        self.db_host: str = os.getenv("DB_HOST", "localhost")
        self.db_port: int = int(os.getenv("DB_PORT", "5432"))
        self.db_name: str = os.getenv("DB_NAME", "product_reviews")
        self.db_user: str = os.getenv("DB_USER", "postgres")
        self.db_password: str = os.getenv("DB_PASSWORD", "password")
        
        # FastAPI settings
        self.app_title: str = os.getenv("APP_TITLE", "Product Reviews API")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
        
        # API settings
        self.api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
        
        # Pagination defaults
        self.default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
        self.max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
        
    @property
    def database_url(self) -> str:
        """Get database URL for PostgreSQL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# Global settings instance
settings = Settings()

