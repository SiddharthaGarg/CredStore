"""Database models using Peewee ORM."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from peewee import (
    Model, PostgresqlDatabase, UUIDField, CharField, TextField, IntegerField,
    FloatField, ForeignKeyField, BooleanField, DateTimeField
)

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


class User(BaseModel):
    """User model."""
    
    name = CharField(max_length=255, null=False)
    email = CharField(max_length=255, unique=True, null=False)
    profile = TextField(null=True, help_text="S3 URL for profile image")
    
    class Meta:
        table_name = 'users'
        indexes = (
            (('email',), True),  # Unique index
        )
    
    def __str__(self):
        return f"User({self.name}, {self.email})"


class Review(BaseModel):
    """Review model."""
    
    product_id = CharField(max_length=255, null=False, help_text="References external product (MongoDB ObjectId)")
    user = ForeignKeyField(User, backref='reviews', null=False)
    rating = IntegerField(null=False, help_text="Rating from 1-5")
    description = CharField(max_length=255, null=False)
    created_at = DateTimeField(null=False)
    updated_at = DateTimeField(null=False)
    status = CharField(
        max_length=20, 
        default=ReviewStatus.ACTIVE.value,
        choices=[(status.value, status.value) for status in ReviewStatus]
    )
    
    class Meta:
        table_name = 'reviews'
        indexes = (
            (('product_id',), False),
            (('user', 'product_id'), True),  # One review per user per product
            (('created_at',), False),
            (('rating',), False),
            (('status',), False),
        )
    
    def save(self, *args, **kwargs):
        """Override save to update timestamps."""
        now = datetime.now(timezone.utc)
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Review({self.user.name}, {self.product_id}, {self.rating}★)"


class Comment(BaseModel):
    """Comment model."""
    
    review = ForeignKeyField(Review, backref='comments', null=False)
    user = ForeignKeyField(User, backref='user_comments', null=False)
    description = TextField(null=False)
    created_at = DateTimeField(null=False)
    
    class Meta:
        table_name = 'comments'
        indexes = (
            (('review',), False),
            (('user',), False),
            (('created_at',), False),
        )
    
    def save(self, *args, **kwargs):
        """Override save to set created_at timestamp."""
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Comment({self.user.name}, {self.review.id})"


class ReviewMetrics(BaseModel):
    """Review metrics model."""
    
    review = ForeignKeyField(Review, backref='metrics', unique=True, null=False)
    upvotes = IntegerField(default=0)
    downvotes = IntegerField(default=0)
    comments_count = IntegerField(default=0)
    
    class Meta:
        table_name = 'review_metrics'
        indexes = (
            (('review',), True),  # Unique index
        )
    
    def __str__(self):
        return f"ReviewMetrics({self.review.id}, ↑{self.upvotes}, ↓{self.downvotes})"


# List of all models for easy table creation
MODELS = [User, Review, Comment, ReviewMetrics]



def check_tables_exist():
    """Check if all required tables exist in the database."""
    try:
        with database:
            # Check if all model tables exist
            for model in MODELS:
                if not model.table_exists():
                    return False
            return True
    except Exception:
        return False

