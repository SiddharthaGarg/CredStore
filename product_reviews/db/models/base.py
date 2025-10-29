"""Base database models and configuration."""

import uuid
from enum import Enum
from peewee import Model, PostgresqlDatabase, UUIDField

from config import settings


# Initialize database connection
database = PostgresqlDatabase(
    settings.db_name,
    user=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    autorollback=True,
    autoconnect=True
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

