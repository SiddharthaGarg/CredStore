"""Comment Data Access Object."""

import logging
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

from peewee import DoesNotExist
from db.models import Comment, Review, User
from .base_dao import BaseDAO, DAOException

logger = logging.getLogger(__name__)


class CommentDAO(BaseDAO):
    """DAO for Comment operations."""
    
    def __init__(self):
        super().__init__(Comment)
    
    def create_comment(self, review_id: str, user_id: str, description: str) -> Comment:
        """Create a new comment."""
        try:
            return self.create(
                review=UUID(review_id),
                user=UUID(user_id),
                description=description
            )
        except Exception as e:
            logger.error(f"Error creating comment for review {review_id}: {e}")
            raise DAOException(f"Failed to create comment: {e}")
    
    def get_comment_with_user(self, comment_id: str) -> Optional[Comment]:
        """Get comment with user information."""
        try:
            return (Comment
                   .select(Comment, User)
                   .join(User)
                   .where(Comment.id == UUID(comment_id))
                   .first())
        except Exception as e:
            logger.error(f"Error getting comment {comment_id} with user: {e}")
            return None
    
    def get_comments_by_review(self, review_id: str, limit: int = 20, offset: int = 0) -> List[Comment]:
        """Get comments for a review with pagination."""
        try:
            return list(
                Comment
                .select(Comment, User)
                .join(User)
                .where(Comment.review == UUID(review_id))
                .order_by(Comment.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error getting comments for review {review_id}: {e}")
            return []
    
    def get_recent_comments_by_review(self, review_id: str, limit: int = 5) -> List[Comment]:
        """Get recent comments for a review (for review response)."""
        try:
            return list(
                Comment
                .select(Comment, User)
                .join(User)
                .where(Comment.review == UUID(review_id))
                .order_by(Comment.created_at.desc())
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error getting recent comments for review {review_id}: {e}")
            return []
    
