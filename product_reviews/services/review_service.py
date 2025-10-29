"""Review service for business logic."""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict

from api.schemas import (
    ReviewCreate, ReviewUpdate, ReviewResponse, CommentsSection,
    CommentData, UserDetails
)
from .base_service import BaseService, ServiceException, ValidationException, NotFoundException
from .product_validation_service import product_validator
from db.dao import ReviewDAO, UserDAO, MetricsDAO, CommentDAO
from events import EventBus, ReviewCreated, ReviewUpdated, ReviewDeleted

logger = logging.getLogger(__name__)


class ReviewService(BaseService):
    """Service for review operations."""
    
    def __init__(
        self, 
        review_dao: ReviewDAO = None, 
        user_dao: UserDAO = None, 
        metrics_dao: MetricsDAO = None, 
        comment_dao: CommentDAO = None,
        event_bus: EventBus = None
    ):
        super().__init__(user_dao)
        self.review_dao = review_dao or ReviewDAO()
        self.metrics_dao = metrics_dao or MetricsDAO()
        self.comment_dao = comment_dao or CommentDAO()
        self.event_bus = event_bus
    
    async def create_review(self, product_id: str, review_data: ReviewCreate) -> ReviewResponse:
        """Create a new review."""
        try:
            if not await self.validate_user_exists(review_data.user_id):
                raise ValidationException("Invalid user ID")
            
            if not await product_validator.product_exists(product_id):
                raise ValidationException("Product not found")
            
            if self.review_dao.get_by_user_and_product(review_data.user_id, product_id):
                raise ValidationException("User has already reviewed this product")
            
            review = self.review_dao.create_review(
                product_id=product_id,
                user_id=review_data.user_id,
                rating=review_data.rating,
                description=review_data.description
            )
            
            self.metrics_dao.create_metrics(str(review.id))
            
            self._emit_review_created_event(
                product_id=product_id,
                review_id=str(review.id),
                user_id=review_data.user_id,
                rating=review_data.rating
            )
            
            self._log_operation("Create review", str(review.id), True)
            return await self.get_review_response(review)
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating review: {e}")
            raise ServiceException("Failed to create review")
    
    async def get_reviews_by_product(
        self, 
        product_id: str, 
        page: int = 1, 
        limit: int = 20
    ) -> List[ReviewResponse]:
        """Get reviews for a product with pagination."""
        try:
            offset = (page - 1) * limit
            reviews = self.review_dao.get_reviews_by_product(product_id, limit, offset)
            
            review_responses = []
            for review in reviews:
                review_response = await self.get_review_response(review)
                review_responses.append(review_response)
            
            return review_responses
            
        except Exception as e:
            logger.error(f"Error getting reviews for product {product_id}: {e}")
            raise ServiceException("Failed to retrieve reviews")
    
    async def update_review(self, review_id: str, update_data: ReviewUpdate) -> ReviewResponse:
        """Update a review."""
        try:
            review = self.review_dao.get_review_with_user(review_id)
            if not review:
                raise NotFoundException("Review", review_id)
            
            review = self.review_dao.update_review(
                review, 
                rating=update_data.rating,
                description=update_data.description
            )
            
            if update_data.upvotes is not None or update_data.downvotes is not None:
                self.metrics_dao.update_votes(
                    review_id, 
                    upvotes=update_data.upvotes,
                    downvotes=update_data.downvotes
                )
            
            if update_data.rating is not None:
                self._emit_review_updated_event(
                    product_id=review.product_id,
                    review_id=review_id,
                    rating=update_data.rating
                )
            
            self._log_operation("Update review", review_id, True)
            return await self.get_review_response(review)
            
        except (ValidationException, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"Error updating review {review_id}: {e}")
            raise ServiceException("Failed to update review")
    
    async def delete_review(self, review_id: str) -> bool:
        """Delete a review (hard delete)."""
        try:
            review = self.review_dao.get_review_with_user(review_id)
            if not review:
                raise NotFoundException("Review", review_id)
            
            product_id = review.product_id
            
            self.review_dao.delete(review)
            
            self._emit_review_deleted_event(
                product_id=product_id,
                review_id=review_id
            )
            
            self._log_operation("Delete review", review_id, True)
            return True
            
        except (ValidationException, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"Error deleting review {review_id}: {e}")
            raise ServiceException("Failed to delete review")
    
    async def get_review_response(self, review) -> ReviewResponse:
        """Convert review to response format."""
        try:
            user_details = UserDetails(
                id=str(review.user.id),
                name=review.user.name,
                profile=review.user.profile
            )
            
            metrics = self.metrics_dao.get_metrics_by_review(str(review.id))
            recent_comments = self.comment_dao.get_recent_comments_by_review(str(review.id), 5)
            
            comment_data = []
            for comment in recent_comments:
                comment_user_details = UserDetails(
                    id=str(comment.user.id),
                    name=comment.user.name,
                    profile=comment.user.profile
                )
                
                comment_data.append(CommentData(
                    id=str(comment.id),
                    user_details=comment_user_details,
                    description=comment.description
                ))
            
            comments_section = CommentsSection(
                total=metrics.comments_count if metrics else 0,
                data=comment_data
            )
            
            return ReviewResponse(
                id=str(review.id),
                user_details=user_details,
                rating=review.rating,
                description=review.description,
                upvotes=metrics.upvotes if metrics else 0,
                downvotes=metrics.downvotes if metrics else 0,
                comments=comments_section,
                created_at=review.created_at,
                updated_at=review.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error creating review response: {e}")
            raise ServiceException("Failed to format review response")
    
    def _emit_review_created_event(self, product_id: str, review_id: str, user_id: str, rating: int):
        """Emit ReviewCreated event."""
        if self.event_bus is None:
            logger.debug("Event bus not available, skipping event emission")
            return
        
        try:
            self.event_bus.publish(ReviewCreated(
                product_id=product_id,
                review_id=review_id,
                user_id=user_id,
                rating=rating,
                timestamp=datetime.now(timezone.utc)
            ))
            logger.debug(f"Emitted ReviewCreated event for review {review_id}")
        except Exception as e:
            logger.error(f"Error emitting ReviewCreated event: {e}", exc_info=True)
    
    def _emit_review_updated_event(self, product_id: str, review_id: str, rating: int):
        """Emit ReviewUpdated event."""
        if self.event_bus is None:
            logger.debug("Event bus not available, skipping event emission")
            return
        
        try:
            self.event_bus.publish(ReviewUpdated(
                product_id=product_id,
                review_id=review_id,
                rating=rating,
                timestamp=datetime.now(timezone.utc)
            ))
            logger.debug(f"Emitted ReviewUpdated event for review {review_id}")
        except Exception as e:
            logger.error(f"Error emitting ReviewUpdated event: {e}", exc_info=True)
    
    def _emit_review_deleted_event(self, product_id: str, review_id: str):
        """Emit ReviewDeleted event."""
        if self.event_bus is None:
            logger.debug("Event bus not available, skipping event emission")
            return
        
        try:
            self.event_bus.publish(ReviewDeleted(
                product_id=product_id,
                review_id=review_id,
                timestamp=datetime.now(timezone.utc)
            ))
            logger.debug(f"Emitted ReviewDeleted event for review {review_id}")
        except Exception as e:
            logger.error(f"Error emitting ReviewDeleted event: {e}", exc_info=True)

