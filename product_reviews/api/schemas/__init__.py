"""API schemas package - exports all schema classes."""

# Common/base schemas
from .common import ErrorResponse, APIResponse, UserDetails

# Review schemas
from .reviews import (
    ReviewCreate,
    ReviewUpdate,
    CommentsSection,
    ReviewResponse,
    ReviewListResponse,
    ReviewDetailResponse,
)

# Comment schemas
from .comments import (
    CommentCreate,
    CommentData,
    CommentResponse,
    CommentListResponse,
)

# Metrics schemas
from .metrics import (
    RatingDistribution,
    ReviewMetricsData,
    ReviewMetricsResponse,
)

# Pagination schemas
from .pagination import (
    PaginationParams,
    SuccessResponse,
)

__all__ = [
    # Common
    "ErrorResponse",
    "APIResponse",
    "UserDetails",
    # Reviews
    "ReviewCreate",
    "ReviewUpdate",
    "CommentsSection",
    "ReviewResponse",
    "ReviewListResponse",
    "ReviewDetailResponse",
    # Comments
    "CommentCreate",
    "CommentData",
    "CommentResponse",
    "CommentListResponse",
    # Metrics
    "RatingDistribution",
    "ReviewMetricsData",
    "ReviewMetricsResponse",
    # Pagination
    "PaginationParams",
    "SuccessResponse",
]

