"""Metrics service for review analytics."""

import logging
from typing import Dict

from api.schemas import RatingDistribution, ReviewMetricsData
from .base_service import BaseService, ServiceException, ValidationException
from db.dao import ReviewDAO, MetricsDAO, UserDAO

logger = logging.getLogger(__name__)


class MetricsService(BaseService):
    """Service for review metrics and analytics."""
    
    def __init__(self, review_dao: ReviewDAO = None, metrics_dao: MetricsDAO = None, user_dao: UserDAO = None):
        super().__init__(user_dao)
        self.review_dao = review_dao or ReviewDAO()
        self.metrics_dao = metrics_dao or MetricsDAO()
    
    async def get_review_summary_stats(self, product_id: str) -> Dict[str, any]:
        """Get summary statistics for product reviews."""
        try:
            total_reviews = self.review_dao.get_review_count_by_product(product_id)
            
            if total_reviews == 0:
                return {
                    "total_reviews": 0,
                    "average_rating": 0.0,
                    "rating_distribution": {str(i): 0 for i in range(1, 6)}
                }
            
            avg_rating = self.review_dao.get_average_rating(product_id)
            rating_distribution = self.review_dao.get_rating_distribution(product_id)
            
            return {
                "total_reviews": total_reviews,
                "average_rating": avg_rating,
                "rating_distribution": rating_distribution
            }
            
        except Exception as e:
            logger.error(f"Error getting summary stats for product {product_id}: {e}")
            raise ServiceException("Failed to get review summary statistics")

