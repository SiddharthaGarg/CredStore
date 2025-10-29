"""Review database model."""

from datetime import datetime, timezone
from peewee import CharField, IntegerField, ForeignKeyField, DateTimeField

from .base import BaseModel, ReviewStatus
from .user import User


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

