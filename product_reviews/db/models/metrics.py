"""Review metrics database model."""

from peewee import ForeignKeyField, IntegerField

from .base import BaseModel
from .review import Review


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

