"""API request and response schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# Base schemas
class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    code: str
    message: str


class APIResponse(BaseModel):
    """Base API response with error handling."""
    
    data: Optional[Any] = None
    err: Optional[ErrorResponse] = None


# User schemas
class UserDetails(BaseModel):
    """User details for nested responses."""
    
    id: str
    name: str
    profile: Optional[str] = None


# Review schemas
class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    
    user_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    description: str = Field(..., max_length=255, description="Review description")
    
    @field_validator('user_id')
    def validate_user_id(cls, v):
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError("user_id must be a valid UUID")


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    
    rating: Optional[int] = Field(None, ge=1, le=5)
    description: Optional[str] = Field(None, max_length=255)
    upvotes: Optional[int] = Field(None, ge=0)
    downvotes: Optional[int] = Field(None, ge=0)


class CommentData(BaseModel):
    """Comment data in nested responses."""
    
    id: str
    user_details: UserDetails
    description: str


class CommentsSection(BaseModel):
    """Comments section with total count and recent comments."""
    
    total: int
    data: List[CommentData]


class ReviewResponse(BaseModel):
    """Individual review response."""
    
    id: str
    user_details: UserDetails
    rating: int
    description: str
    upvotes: int
    downvotes: int
    comments: CommentsSection
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(APIResponse):
    """Response for listing reviews."""
    
    data: Optional[List[ReviewResponse]] = None


class ReviewDetailResponse(APIResponse):
    """Response for single review details."""
    
    data: Optional[ReviewResponse] = None


# Comment schemas
class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    
    description: str = Field(..., min_length=1, description="Comment description")
    user_id: str
    
    @field_validator('user_id')
    def validate_user_id(cls, v):
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError("user_id must be a valid UUID")


class CommentResponse(BaseModel):
    """Individual comment response."""
    
    id: str
    user_details: UserDetails
    description: str
    created_at: datetime


class CommentListResponse(APIResponse):
    """Response for listing comments."""
    
    data: Optional[List[CommentResponse]] = None


# Review metrics schemas
class RatingDistribution(BaseModel):
    """Rating distribution for review metrics."""
    
    field_1: int = Field(alias="1", description="Number of 1-star ratings")
    field_2: int = Field(alias="2", description="Number of 2-star ratings")
    field_3: int = Field(alias="3", description="Number of 3-star ratings")
    field_4: int = Field(alias="4", description="Number of 4-star ratings")
    field_5: int = Field(alias="5", description="Number of 5-star ratings")
    
    class Config:
        populate_by_name = True


class ReviewMetricsData(BaseModel):
    """Review metrics data."""
    
    ratings: RatingDistribution


class ReviewMetricsResponse(APIResponse):
    """Response for review metrics."""
    
    data: Optional[ReviewMetricsData] = None


# Pagination schemas
class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


# Success response for operations
class SuccessResponse(APIResponse):
    """Success response for operations like create, update, delete."""
    
    data: Optional[Dict[str, str]] = None

