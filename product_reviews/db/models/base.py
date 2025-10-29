"""Base database models and configuration."""

import uuid
from enum import Enum
from peewee import Model, PostgresqlDatabase, UUIDField

# Initialize database connection with autoconnect=False
# Connection will be established by DatabaseManager
database = PostgresqlDatabase(
    None,  # Will be set by DatabaseManager.connect()
    autoconnect=False  # Don't connect at import time
)


class ReviewStatus(Enum):
    """Review status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class BaseModel(Model):
    """Base model with common fields."""
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    
    class Meta:
        database = database

