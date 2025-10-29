"""Review Metrics Data Access Object."""

import logging
from typing import Optional, List, Dict
from uuid import UUID

from peewee import DoesNotExist
from models import ReviewMetrics, Review
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
    
    def update_upvotes(self, review_id: str, upvotes: int) -> Optional[ReviewMetrics]:
        """Update upvotes for a review."""
        try:
            metrics = self.get_metrics_by_review(review_id)
            if metrics:
                return self.update(metrics, upvotes=upvotes)
            return None
        except Exception as e:
            logger.error(f"Error updating upvotes for review {review_id}: {e}")
            return None
    
    def update_downvotes(self, review_id: str, downvotes: int) -> Optional[ReviewMetrics]:
        """Update downvotes for a review."""
        try:
            metrics = self.get_metrics_by_review(review_id)
            if metrics:
                return self.update(metrics, downvotes=downvotes)
            return None
        except Exception as e:
            logger.error(f"Error updating downvotes for review {review_id}: {e}")
            return None
    
    def update_comments_count(self, review_id: str, comments_count: int) -> Optional[ReviewMetrics]:
        """Update comments count for a review."""
        try:
            metrics = self.get_metrics_by_review(review_id)
            if metrics:
                return self.update(metrics, comments_count=comments_count)
            return None
        except Exception as e:
            logger.error(f"Error updating comments count for review {review_id}: {e}")
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
    
    def decrement_comments_count(self, review_id: str) -> Optional[ReviewMetrics]:
        """Decrement comments count by 1."""
        try:
            metrics = self.get_metrics_by_review(review_id)
            if metrics:
                new_count = max(0, metrics.comments_count - 1)
                return self.update(metrics, comments_count=new_count)
            return None
        except Exception as e:
            logger.error(f"Error decrementing comments count for review {review_id}: {e}")
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
    
    def get_metrics_by_review_ids(self, review_ids: List[str]) -> Dict[str, ReviewMetrics]:
        """Get metrics for multiple reviews."""
        try:
            uuid_ids = [UUID(rid) for rid in review_ids]
            metrics_list = list(
                ReviewMetrics
                .select()
                .where(ReviewMetrics.review.in_(uuid_ids))
            )
            
            # Create a dictionary mapping review_id to metrics
            metrics_dict = {}
            for metrics in metrics_list:
                review_id = str(metrics.review.id)
                metrics_dict[review_id] = metrics
            
            return metrics_dict
        except Exception as e:
            logger.error(f"Error getting metrics by review IDs: {e}")
            return {}
