"""Review Data Access Object."""

import logging
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

from peewee import DoesNotExist, fn
from models import Review, User, ReviewStatus
from .base_dao import BaseDAO, DAOException

logger = logging.getLogger(__name__)


class ReviewDAO(BaseDAO):
    """DAO for Review operations."""
    
    def __init__(self):
        super().__init__(Review)
    
    def create_review(self, product_id: str, user_id: str, rating: int, description: str) -> Review:
        """Create a new review."""
        try:
            return self.create(
                product_id=product_id,
                user=UUID(user_id),
                rating=rating,
                description=description,
                status=ReviewStatus.ACTIVE.value
            )
        except Exception as e:
            logger.error(f"Error creating review for product {product_id}: {e}")
            raise DAOException(f"Failed to create review: {e}")
    
    def get_review_with_user(self, review_id: str) -> Optional[Review]:
        """Get review with user information."""
        try:
            return (Review
                   .select(Review, User)
                   .join(User)
                   .where(Review.id == UUID(review_id))
                   .first())
        except Exception as e:
            logger.error(f"Error getting review {review_id} with user: {e}")
            return None
    
    def get_reviews_by_product(self, product_id: str, limit: int = 20, offset: int = 0) -> List[Review]:
        """Get reviews for a product with pagination."""
        try:
            return list(
                Review
                .select(Review, User)
                .join(User)
                .where(
                    (Review.product_id == product_id) &
                    (Review.status == ReviewStatus.ACTIVE.value)
                )
                .order_by(Review.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error getting reviews for product {product_id}: {e}")
            return []
    
    def get_reviews_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Review]:
        """Get reviews by a specific user."""
        try:
            return list(
                Review
                .select()
                .where(
                    (Review.user == UUID(user_id)) &
                    (Review.status == ReviewStatus.ACTIVE.value)
                )
                .order_by(Review.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error getting reviews by user {user_id}: {e}")
            return []
    
    def update_review(self, review: Review, rating: int = None, description: str = None) -> Review:
        """Update review content."""
        try:
            update_data = {}
            if rating is not None:
                update_data['rating'] = rating
            if description is not None:
                update_data['description'] = description
            
            if update_data:
                update_data['updated_at'] = datetime.now()
                return self.update(review, **update_data)
            return review
        except Exception as e:
            logger.error(f"Error updating review {review.id}: {e}")
            raise DAOException(f"Failed to update review: {e}")
    
    def soft_delete_review(self, review: Review) -> Review:
        """Soft delete a review by changing status."""
        try:
            return self.update(review, status=ReviewStatus.INACTIVE.value, updated_at=datetime.now())
        except Exception as e:
            logger.error(f"Error soft deleting review {review.id}: {e}")
            raise DAOException(f"Failed to delete review: {e}")
    
    def get_rating_distribution(self, product_id: str) -> Dict[str, int]:
        """Get rating distribution for a product."""
        try:
            # Initialize distribution
            distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            
            # Get rating counts
            rating_counts = (Review
                           .select(Review.rating, fn.COUNT(Review.id).alias('count'))
                           .where(
                               (Review.product_id == product_id) &
                               (Review.status == ReviewStatus.ACTIVE.value)
                           )
                           .group_by(Review.rating))
            
            for rating_count in rating_counts:
                distribution[str(rating_count.rating)] = rating_count.count
            
            return distribution
        except Exception as e:
            logger.error(f"Error getting rating distribution for product {product_id}: {e}")
            return {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    
    def user_has_reviewed_product(self, user_id: str, product_id: str) -> bool:
        """Check if user has already reviewed a product."""
        try:
            return (Review
                   .select()
                   .where(
                       (Review.user == UUID(user_id)) &
                       (Review.product_id == product_id)
                   )
                   .exists())
        except Exception as e:
            logger.error(f"Error checking if user {user_id} reviewed product {product_id}: {e}")
            return False
    
    def get_review_count_by_product(self, product_id: str) -> int:
        """Get total review count for a product."""
        try:
            return (Review
                   .select()
                   .where(
                       (Review.product_id == product_id) &
                       (Review.status == ReviewStatus.ACTIVE.value)
                   )
                   .count())
        except Exception as e:
            logger.error(f"Error getting review count for product {product_id}: {e}")
            return 0
    
    def get_average_rating(self, product_id: str) -> float:
        """Get average rating for a product."""
        try:
            result = (Review
                     .select(fn.AVG(Review.rating).alias('avg_rating'))
                     .where(
                         (Review.product_id == product_id) &
                         (Review.status == ReviewStatus.ACTIVE.value)
                     )
                     .scalar())
            return round(float(result or 0), 2)
        except Exception as e:
            logger.error(f"Error getting average rating for product {product_id}: {e}")
            return 0.0
