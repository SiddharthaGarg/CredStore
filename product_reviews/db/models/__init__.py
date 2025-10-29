"""Database models package - exports all models."""

from .base import database, BaseModel, ReviewStatus
from .user import User
from .review import Review
from .comment import Comment
from .metrics import ReviewMetrics

MODELS = [User, Review, Comment, ReviewMetrics]


def check_tables_exist():
    """Check if all required tables exist in the database.
    """
    try:
        for model in MODELS:
            if not model.table_exists():
                return False
        return True
    except Exception:
        return False


__all__ = [
    "database",
    "BaseModel",
    "ReviewStatus",
    "User",
    "Review",
    "Comment",
    "ReviewMetrics",
    "MODELS",
    "check_tables_exist",
]

