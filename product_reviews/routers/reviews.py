"""Reviews API router."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query, Path, status, Depends
from fastapi.responses import JSONResponse

from config import settings
from schemas import (
    ReviewCreate, ReviewUpdate, ReviewListResponse, ReviewDetailResponse,
    ReviewMetricsResponse, CommentCreate, CommentListResponse, 
    PaginationParams, SuccessResponse, ErrorResponse, APIResponse
)
from services import ReviewService, CommentService, MetricsService
from services.base_service import (
    ServiceException, ValidationException, NotFoundException, PermissionException
)
from events import event_bus

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/reviews", tags=["reviews"])

# Service instances
# Initialize services with dependency injection
review_service = ReviewService(event_bus=event_bus)
comment_service = CommentService()
metrics_service = MetricsService()


async def handle_service_exceptions(func, *args, **kwargs):
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


@router.get("/{product_id}/metrics", response_model=ReviewMetricsResponse)
async def get_review_metrics(
    product_id: str = Path(..., description="Product ID")
):
    """Get cumulative metrics of all reviews on a product."""
    try:
        metrics_data = await handle_service_exceptions(
            metrics_service.get_product_review_metrics, product_id
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


@router.get("/{product_id}", response_model=ReviewListResponse)
async def get_reviews(
    product_id: str = Path(..., description="Product ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get reviews for a product with pagination."""
    try:
        reviews = await handle_service_exceptions(
            review_service.get_reviews_by_product, product_id, page, limit
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


@router.post("/{product_id}", response_model=ReviewDetailResponse, status_code=status.HTTP_201_CREATED)
async def add_review(
    product_id: str = Path(..., description="Product ID"),
    review_data: ReviewCreate = ...
):
    """Add a new review for a product."""
    try:
        review_response = await handle_service_exceptions(
            review_service.create_review, product_id, review_data
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


@router.put("/{review_id}", response_model=ReviewDetailResponse)
async def update_review(
    review_id: str = Path(..., description="Review ID"),
    update_data: ReviewUpdate = ...
):
    """Update a review."""
    try:
        review_response = await handle_service_exceptions(
            review_service.update_review, review_id, update_data
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


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str = Path(..., description="Review ID")
):
    """Delete a review."""
    try:
        await handle_service_exceptions(
            review_service.delete_review, review_id
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


@router.post("/{review_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(
    review_id: str = Path(..., description="Review ID"),
    comment_data: CommentCreate = ...
):
    """Add a comment to a review."""
    try:
        success = await handle_service_exceptions(
            comment_service.create_comment, review_id, comment_data
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


@router.get("/{review_id}/comments", response_model=CommentListResponse)
async def get_review_comments(
    review_id: str = Path(..., description="Review ID"),
    page: int = Query(1, ge=1, description="Page number"),  
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get comments for a review with pagination."""
    try:
        comments = await handle_service_exceptions(
            comment_service.get_comments_by_review, review_id, page, limit
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


# Additional endpoints for completeness

@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review_by_id(
    review_id: str = Path(..., description="Review ID")
):
    """Get a specific review by ID."""
    try:
        review = await handle_service_exceptions(
            review_service.get_by_id, review_id
        )
        
        if not review:
            raise NotFoundException("Review", review_id)
        
        review_response = await handle_service_exceptions(
            review_service.get_review_response, review
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

