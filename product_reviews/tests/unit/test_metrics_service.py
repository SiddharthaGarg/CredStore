"""Unit tests for MetricsService."""

import pytest
from unittest.mock import Mock

from services.metrics_service import MetricsService
from services.base_service import ServiceException


@pytest.fixture
def mock_review_dao():
    """Mock ReviewDAO."""
    return Mock()


@pytest.fixture
def mock_metrics_dao():
    """Mock MetricsDAO."""
    return Mock()


@pytest.fixture
def mock_user_dao():
    """Mock UserDAO."""
    return Mock()


@pytest.fixture
def metrics_service(mock_review_dao, mock_metrics_dao, mock_user_dao):
    """Create MetricsService instance with mocked DAOs."""
    return MetricsService(
        review_dao=mock_review_dao,
        metrics_dao=mock_metrics_dao,
        user_dao=mock_user_dao
    )


class TestMetricsServiceInit:
    """Test MetricsService initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default DAOs."""
        service = MetricsService()
        assert service.review_dao is not None
        assert service.metrics_dao is not None

    def test_init_with_custom_daos(self, mock_review_dao, mock_metrics_dao, mock_user_dao):
        """Test initialization with custom DAOs."""
        service = MetricsService(
            review_dao=mock_review_dao,
            metrics_dao=mock_metrics_dao,
            user_dao=mock_user_dao
        )
        assert service.review_dao == mock_review_dao
        assert service.metrics_dao == mock_metrics_dao


class TestGetReviewSummaryStats:
    """Test get_review_summary_stats method."""

    @pytest.mark.asyncio
    async def test_get_review_summary_stats_success(
        self, metrics_service, mock_review_dao
    ):
        """Test successful retrieval of summary stats."""
        mock_review_dao.get_review_count_by_product = Mock(return_value=10)
        mock_review_dao.get_average_rating = Mock(return_value=4.5)
        mock_review_dao.get_rating_distribution = Mock(return_value={
            "1": 0,
            "2": 1,
            "3": 2,
            "4": 3,
            "5": 4
        })
        
        result = await metrics_service.get_review_summary_stats("product123")
        
        assert result["total_reviews"] == 10
        assert result["average_rating"] == 4.5
        assert result["rating_distribution"]["1"] == 0
        assert result["rating_distribution"]["2"] == 1
        assert result["rating_distribution"]["3"] == 2
        assert result["rating_distribution"]["4"] == 3
        assert result["rating_distribution"]["5"] == 4
        mock_review_dao.get_review_count_by_product.assert_called_once_with("product123")
        mock_review_dao.get_average_rating.assert_called_once_with("product123")
        mock_review_dao.get_rating_distribution.assert_called_once_with("product123")

    @pytest.mark.asyncio
    async def test_get_review_summary_stats_zero_reviews(
        self, metrics_service, mock_review_dao
    ):
        """Test get_review_summary_stats when no reviews exist."""
        mock_review_dao.get_review_count_by_product = Mock(return_value=0)
        
        result = await metrics_service.get_review_summary_stats("product123")
        
        assert result["total_reviews"] == 0
        assert result["average_rating"] == 0.0
        assert result["rating_distribution"] == {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0
        }
        mock_review_dao.get_average_rating.assert_not_called()
        mock_review_dao.get_rating_distribution.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_review_summary_stats_partial_distribution(
        self, metrics_service, mock_review_dao
    ):
        """Test get_review_summary_stats with partial rating distribution."""
        mock_review_dao.get_review_count_by_product = Mock(return_value=5)
        mock_review_dao.get_average_rating = Mock(return_value=3.8)
        mock_review_dao.get_rating_distribution = Mock(return_value={
            "1": 0,
            "3": 2,
            "5": 3
        })
        
        result = await metrics_service.get_review_summary_stats("product123")
        
        assert result["total_reviews"] == 5
        assert result["average_rating"] == 3.8
        assert result["rating_distribution"]["1"] == 0
        assert result["rating_distribution"].get("2", 0) == 0  # Missing from distribution
        assert result["rating_distribution"]["3"] == 2
        assert result["rating_distribution"].get("4", 0) == 0  # Missing from distribution
        assert result["rating_distribution"]["5"] == 3

    @pytest.mark.asyncio
    async def test_get_review_summary_stats_exception(
        self, metrics_service, mock_review_dao
    ):
        """Test get_review_summary_stats when exception occurs."""
        mock_review_dao.get_review_count_by_product = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to get review summary statistics"):
            await metrics_service.get_review_summary_stats("product123")

