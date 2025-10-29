"""Review-related request and response schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from .common import APIResponse, UserDetails
from .comments import CommentData


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

