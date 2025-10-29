"""Common/base schemas for API responses."""

from typing import Optional, Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    code: str
    message: str


class APIResponse(BaseModel):
    """Base API response with error handling."""
    
    data: Optional[Any] = None
    err: Optional[ErrorResponse] = None


class UserDetails(BaseModel):
    """User details for nested responses."""
    
    id: str
    name: str
    profile: Optional[str] = None

