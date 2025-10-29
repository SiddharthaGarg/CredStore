"""Pagination-related schemas."""

from typing import Dict, Optional
from pydantic import BaseModel, Field

from .common import APIResponse


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class SuccessResponse(APIResponse):
    """Success response for operations like create, update, delete."""
    
    data: Optional[Dict[str, str]] = None

