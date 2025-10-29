"""Configuration settings for the homepage module."""

import os
from typing import Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class Settings:
    """Application settings."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize settings.
        
        Args:
            env_file: Optional path to .env file to load. If None, uses default .env
                     or reads from environment variables only.
        """
        if env_file:
            if load_dotenv is None:
                raise ImportError("python-dotenv is required to load .env files")
            load_dotenv(env_file, override=True)
        elif load_dotenv:
            # Try loading default .env file if it exists
            default_env = Path(".env")
            if default_env.exists():
                load_dotenv(default_env, override=False)
        
        # MongoDB settings
        self.mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_database: str = os.getenv("MONGODB_DATABASE", "appstore")
        self.mongodb_collection: str = os.getenv("MONGODB_COLLECTION", "products")
        
        # Elasticsearch settings
        self.elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.elasticsearch_index: str = os.getenv("ELASTICSEARCH_INDEX", "products")
        
        # FastAPI settings
        self.app_title: str = os.getenv("APP_TITLE", "App Store Homepage API")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")


# Global settings instance (default - loads .env if exists)
settings = Settings()
