"""Review Metrics Data Access Object."""

import logging
from typing import Optional, List, Dict
from uuid import UUID

from peewee import DoesNotExist
from db.models import ReviewMetrics, Review
from .base_dao import BaseDAO, DAOException

logger = logging.getLogger(__name__)


class MetricsDAO(BaseDAO):
    """DAO for ReviewMetrics operations."""
    
    def __init__(self):
        super().__init__(ReviewMetrics)
    
    def create_metrics(self, review_id: str, upvotes: int = 0, downvotes: int = 0, comments_count: int = 0) -> ReviewMetrics:
        """Create metrics for a review."""
        try:
            return self.create(
                review=UUID(review_id),
                upvotes=upvotes,
                downvotes=downvotes,
                comments_count=comments_count
            )
        except Exception as e:
            logger.error(f"Error creating metrics for review {review_id}: {e}")
            raise DAOException(f"Failed to create metrics: {e}")
    
    def get_metrics_by_review(self, review_id: str) -> Optional[ReviewMetrics]:
        """Get metrics for a specific review."""
        try:
            return ReviewMetrics.get(ReviewMetrics.review == UUID(review_id))
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting metrics for review {review_id}: {e}")
            return None
    
    def increment_comments_count(self, review_id: str) -> Optional[ReviewMetrics]:
        """Increment comments count by 1."""
        try:
            metrics = self.get_metrics_by_review(review_id)
            if metrics:
                new_count = metrics.comments_count + 1
                return self.update(metrics, comments_count=new_count)
            return None
        except Exception as e:
            logger.error(f"Error incrementing comments count for review {review_id}: {e}")
            return None
    
    def update_votes(self, review_id: str, upvotes: int = None, downvotes: int = None) -> Optional[ReviewMetrics]:
        """Update both upvotes and downvotes."""
        try:
            metrics = self.get_metrics_by_review(review_id)
            if metrics:
                update_data = {}
                if upvotes is not None:
                    update_data['upvotes'] = upvotes
                if downvotes is not None:
                    update_data['downvotes'] = downvotes
                
                if update_data:
                    return self.update(metrics, **update_data)
            return metrics
        except Exception as e:
            logger.error(f"Error updating votes for review {review_id}: {e}")
            return None
