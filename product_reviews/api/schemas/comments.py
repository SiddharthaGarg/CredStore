"""Comment-related request and response schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from .common import APIResponse, UserDetails


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


class CommentData(BaseModel):
    """Comment data in nested responses."""
    
    id: str
    user_details: UserDetails
    description: str


class CommentResponse(BaseModel):
    """Individual comment response."""
    
    id: str
    user_details: UserDetails
    description: str
    created_at: datetime


class CommentListResponse(APIResponse):
    """Response for listing comments."""
    
    data: Optional[List[CommentResponse]] = None

