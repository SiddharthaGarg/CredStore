"""Reviews API router."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from config import settings
from api.schemas import (
    ReviewCreate, ReviewUpdate, ReviewListResponse, ReviewDetailResponse,
    ReviewMetricsResponse, ReviewMetricsData, RatingDistribution,
    CommentCreate, CommentListResponse, 
    ErrorResponse
)
from services import ReviewService, CommentService, MetricsService
from services.base_service import (
    ServiceException, ValidationException, NotFoundException, PermissionException
)
from events import event_bus
from db.dao import ReviewDAO

logger = logging.getLogger(__name__)


class ReviewRouter:
    """Class-based router for review endpoints."""
    
    def __init__(self):
        """Initialize router with dependencies."""
        self.review_service = ReviewService(event_bus=event_bus)
        self.comment_service = CommentService()
        self.metrics_service = MetricsService()
        
        self.router = APIRouter(prefix="/reviews", tags=["reviews"])
        
        self._register_routes()
    
    def _register_routes(self):
        """Register all route handlers."""
        self.router.add_api_route(
            "/{product_id}/metrics",
            self.get_review_metrics,
            methods=["GET"],
            response_model=ReviewMetricsResponse
        )
        self.router.add_api_route(
            "/{product_id}",
            self.get_reviews,
            methods=["GET"],
            response_model=ReviewListResponse
        )
        self.router.add_api_route(
            "/{product_id}",
            self.add_review,
            methods=["POST"],
            response_model=ReviewDetailResponse,
            status_code=status.HTTP_201_CREATED
        )
        self.router.add_api_route(
            "/{review_id}",
            self.update_review,
            methods=["PUT"],
            response_model=ReviewDetailResponse
        )
        self.router.add_api_route(
            "/{review_id}",
            self.delete_review,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT
        )
        self.router.add_api_route(
            "/{review_id}/comments",
            self.add_comment,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED
        )
        self.router.add_api_route(
            "/{review_id}/comments",
            self.get_review_comments,
            methods=["GET"],
            response_model=CommentListResponse
        )
    
    async def _handle_service_exceptions(self, func, *args, **kwargs):
        """Handle service exceptions and convert to HTTP responses."""
        try:
            return await func(*args, **kwargs)
        except ValidationException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": e.code, "message": e.message}
            )
        except NotFoundException as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": e.code, "message": e.message}
            )
        except PermissionException as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": e.code, "message": e.message}
            )
        except ServiceException as e:
            logger.error(f"Service error: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": e.code, "message": e.message}
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
            )
    
    async def get_review_metrics(
        self,
        product_id: str = Path(..., description="Product ID")
    ):
        """Get cumulative metrics of all reviews on a product."""
        try:
            stats = await self._handle_service_exceptions(
                self.metrics_service.get_review_summary_stats, product_id
            )
            
            ratings = RatingDistribution(
                **{str(i): stats["rating_distribution"].get(str(i), 0) for i in range(1, 6)}
            )
            
            metrics_data = ReviewMetricsData(
                total_reviews=stats["total_reviews"],
                average_rating=stats["average_rating"],
                ratings=ratings
            )
            
            return ReviewMetricsResponse(data=metrics_data, err=None)
            
        except HTTPException as e:
            error_response = ReviewMetricsResponse(
                data=None,
                err=ErrorResponse(code=e.detail["code"], message=e.detail["message"])
            )
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump()
            )
    
    async def get_reviews(
        self,
        product_id: str = Path(..., description="Product ID"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        """Get reviews for a product with pagination."""
        try:
            reviews = await self._handle_service_exceptions(
                self.review_service.get_reviews_by_product, product_id, page, limit
            )
            
            return ReviewListResponse(data=reviews, err=None)
            
        except HTTPException as e:
            error_response = ReviewListResponse(
                data=None,
                err=ErrorResponse(code=e.detail["code"], message=e.detail["message"])
            )
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump()
            )
    
    async def add_review(
        self,
        product_id: str = Path(..., description="Product ID"),
        review_data: ReviewCreate = ...
    ):
        """Add a new review for a product."""
        try:
            review_response = await self._handle_service_exceptions(
                self.review_service.create_review, product_id, review_data
            )
            
            return ReviewDetailResponse(data=review_response, err=None)
            
        except HTTPException as e:
            error_response = ReviewDetailResponse(
                data=None,
                err=ErrorResponse(code=e.detail["code"], message=e.detail["message"])
            )
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump()
            )
    
    async def update_review(
        self,
        review_id: str = Path(..., description="Review ID"),
        update_data: ReviewUpdate = ...
    ):
        """Update a review."""
        try:
            review_response = await self._handle_service_exceptions(
                self.review_service.update_review, review_id, update_data
            )
            
            return ReviewDetailResponse(data=review_response, err=None)
            
        except HTTPException as e:
            error_response = ReviewDetailResponse(
                data=None,
                err=ErrorResponse(code=e.detail["code"], message=e.detail["message"])
            )
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump()
            )
    
    async def delete_review(
        self,
        review_id: str = Path(..., description="Review ID")
    ):
        """Delete a review."""
        try:
            await self._handle_service_exceptions(
                self.review_service.delete_review, review_id
            )
            
            # Return 204 No Content
            return None
            
        except HTTPException as e:
            # For DELETE operations, we still need to return error responses
            error_response = {
                "data": None,
                "err": {"code": e.detail["code"], "message": e.detail["message"]}
            }
            return JSONResponse(
                status_code=e.status_code,
                content=error_response
            )
    
    async def add_comment(
        self,
        review_id: str = Path(..., description="Review ID"),
        comment_data: CommentCreate = ...
    ):
        """Add a comment to a review."""
        try:
            success = await self._handle_service_exceptions(
                self.comment_service.create_comment, review_id, comment_data
            )
            
            if success:
                # Return 201 Created with minimal response
                return JSONResponse(
                    status_code=status.HTTP_201_CREATED,
                    content={"message": "Comment created successfully"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"code": "CREATION_FAILED", "message": "Failed to create comment"}
                )
                
        except HTTPException as e:
            error_response = {
                "data": None,
                "err": {"code": e.detail["code"], "message": e.detail["message"]}
            }
            return JSONResponse(
                status_code=e.status_code,
                content=error_response
            )
    
    async def get_review_comments(
        self,
        review_id: str = Path(..., description="Review ID"),
        page: int = Query(1, ge=1, description="Page number"),  
        limit: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        """Get comments for a review with pagination."""
        try:
            comments = await self._handle_service_exceptions(
                self.comment_service.get_comments_by_review, review_id, page, limit
            )
            
            return CommentListResponse(data=comments, err=None)
            
        except HTTPException as e:
            error_response = CommentListResponse(
                data=None,
                err=ErrorResponse(code=e.detail["code"], message=e.detail["message"])
            )
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump()
            )
    
# Create router instance
_review_router = ReviewRouter()
router = _review_router.router
