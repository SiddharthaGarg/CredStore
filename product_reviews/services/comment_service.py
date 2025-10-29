"""Comment service for business logic."""

import logging
from typing import List, Optional

from api.schemas import CommentCreate, CommentResponse, UserDetails
from .base_service import BaseService, ServiceException, ValidationException, NotFoundException
from db.dao import CommentDAO, ReviewDAO, UserDAO, MetricsDAO

logger = logging.getLogger(__name__)


class CommentService(BaseService):
    """Service for comment operations."""
    
    def __init__(self, comment_dao: CommentDAO = None, review_dao: ReviewDAO = None, 
                 user_dao: UserDAO = None, metrics_dao: MetricsDAO = None):
        super().__init__(user_dao)
        self.comment_dao = comment_dao or CommentDAO()
        self.review_dao = review_dao or ReviewDAO()
        self.metrics_dao = metrics_dao or MetricsDAO()
    
    async def create_comment(self, review_id: str, comment_data: CommentCreate) -> bool:
        """Create a new comment on a review."""
        try:
            if not await self.validate_user_exists(comment_data.user_id):
                raise ValidationException("Invalid user ID")
            
            review = self.review_dao.get_review_with_user(review_id)
            if not review:
                raise NotFoundException("Review", review_id)
            
            if review.status != "active":
                raise ValidationException("Cannot comment on inactive review")
            
            comment = self.comment_dao.create_comment(
                review_id=review_id,
                user_id=comment_data.user_id,
                description=comment_data.description
            )
            
            self.metrics_dao.increment_comments_count(review_id)
            
            self._log_operation("Create comment", str(comment.id), True)
            return True
            
        except (ValidationException, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating comment: {e}")
            raise ServiceException("Failed to create comment")
    
    async def get_comments_by_review(
        self, 
        review_id: str, 
        page: int = 1, 
        limit: int = 20
    ) -> List[CommentResponse]:
        """Get comments for a review with pagination."""
        try:
            review = self.review_dao.get_review_with_user(review_id)
            if not review:
                raise NotFoundException("Review", review_id)
            
            offset = (page - 1) * limit
            comments = self.comment_dao.get_comments_by_review(review_id, limit, offset)
            
            comment_responses = []
            for comment in comments:
                comment_response = await self.get_comment_response(comment)
                comment_responses.append(comment_response)
            
            return comment_responses
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting comments for review {review_id}: {e}")
            raise ServiceException("Failed to retrieve comments")
    
    async def get_comment_response(self, comment) -> CommentResponse:
        """Convert comment to response format."""
        try:
            user_details = UserDetails(
                id=str(comment.user.id),
                name=comment.user.name,
                profile=comment.user.profile
            )
            
            return CommentResponse(
                id=str(comment.id),
                user_details=user_details,
                description=comment.description,
                created_at=comment.created_at
            )
            
        except Exception as e:
            logger.error(f"Error creating comment response: {e}")
            raise ServiceException("Failed to format comment response")
    

