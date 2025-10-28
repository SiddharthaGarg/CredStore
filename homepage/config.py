"""Configuration settings for the homepage module."""

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


# Global settings instance
settings = Settings()
