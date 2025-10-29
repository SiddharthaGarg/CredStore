"""Review metrics-related response schemas."""

from typing import Optional
from pydantic import BaseModel, Field

from .common import APIResponse


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
    
    total_reviews: int = Field(..., description="Total number of reviews")
    average_rating: float = Field(..., description="Average rating")
    ratings: RatingDistribution


class ReviewMetricsResponse(APIResponse):
    """Response for review metrics."""
    
    data: Optional[ReviewMetricsData] = None

