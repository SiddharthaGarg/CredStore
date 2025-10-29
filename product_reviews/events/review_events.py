"""Event models for review operations."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReviewCreated:
    """Event emitted when a review is created."""
    product_id: str
    review_id: str
    user_id: str
    rating: int
    timestamp: datetime


@dataclass
class ReviewUpdated:
    """Event emitted when a review is updated."""
    product_id: str
    review_id: str
    rating: int  # New rating value
    timestamp: datetime


@dataclass
class ReviewDeleted:
    """Event emitted when a review is deleted."""
    product_id: str
    review_id: str
    timestamp: datetime

