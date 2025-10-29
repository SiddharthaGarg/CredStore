"""User database model."""

from peewee import CharField, TextField

from .base import BaseModel


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

