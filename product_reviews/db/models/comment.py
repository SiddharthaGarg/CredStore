"""Comment database model."""

from datetime import datetime, timezone
from peewee import ForeignKeyField, TextField, DateTimeField

from .base import BaseModel
from .user import User
from .review import Review


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

