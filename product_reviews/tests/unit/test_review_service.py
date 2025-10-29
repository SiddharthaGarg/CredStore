"""Unit tests for ReviewService."""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from services.review_service import ReviewService
from services.base_service import ServiceException, ValidationException, NotFoundException
from api.schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from events import EventBus, ReviewCreated


@pytest.fixture
def mock_review_dao():
    """Mock ReviewDAO."""
    return Mock()


@pytest.fixture
def mock_user_dao():
    """Mock UserDAO."""
    return Mock()


@pytest.fixture
def mock_metrics_dao():
    """Mock MetricsDAO."""
    return Mock()


@pytest.fixture
def mock_comment_dao():
    """Mock CommentDAO."""
    return Mock()


@pytest.fixture
def mock_event_bus():
    """Mock EventBus."""
    return Mock(spec=EventBus)


@pytest.fixture
def review_service(mock_review_dao, mock_user_dao, mock_metrics_dao, mock_comment_dao, mock_event_bus):
    """Create ReviewService instance with mocked DAOs."""
    return ReviewService(
        review_dao=mock_review_dao,
        user_dao=mock_user_dao,
        metrics_dao=mock_metrics_dao,
        comment_dao=mock_comment_dao,
        event_bus=mock_event_bus
    )


@pytest.fixture
def mock_review():
    """Mock Review object."""
    user_uuid = uuid4()
    review = MagicMock()
    review.id = uuid4()
    review.product_id = "product123"
    review.user_id = str(user_uuid)
    review.rating = 5
    review.description = "Great product"
    review.created_at = datetime.now(timezone.utc)
    review.updated_at = datetime.now(timezone.utc)
    review.user = MagicMock()
    review.user.id = user_uuid
    review.user.name = "Test User"
    review.user.profile = "http://example.com/profile.jpg"
    return review


@pytest.fixture
def sample_review_create():
    """Sample ReviewCreate object."""
    return ReviewCreate(
        user_id=str(uuid4()),
        rating=5,
        description="Great product"
    )


class TestReviewServiceInit:
    """Test ReviewService initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default DAOs."""
        service = ReviewService()
        assert service.review_dao is not None
        assert service.metrics_dao is not None
        assert service.comment_dao is not None

    def test_init_with_custom_daos(self, mock_review_dao, mock_user_dao, mock_metrics_dao, mock_comment_dao, mock_event_bus):
        """Test initialization with custom DAOs."""
        service = ReviewService(
            review_dao=mock_review_dao,
            user_dao=mock_user_dao,
            metrics_dao=mock_metrics_dao,
            comment_dao=mock_comment_dao,
            event_bus=mock_event_bus
        )
        assert service.review_dao == mock_review_dao
        assert service.metrics_dao == mock_metrics_dao
        assert service.comment_dao == mock_comment_dao
        assert service.event_bus == mock_event_bus


class TestCreateReview:
    """Test create_review method."""

    @pytest.mark.asyncio
    @patch('services.review_service.product_validator')
    async def test_create_review_success(
        self, mock_validator, review_service, mock_review_dao, mock_user_dao,
        mock_metrics_dao, mock_comment_dao, mock_event_bus, sample_review_create, mock_review
    ):
        """Test successful review creation."""
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_validator.product_exists = AsyncMock(return_value=True)
        mock_review_dao.get_by_user_and_product = Mock(return_value=None)
        mock_review_dao.create_review = Mock(return_value=mock_review)
        mock_metrics_dao.create_metrics = Mock()
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=MagicMock(comments_count=0))
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.create_review("product123", sample_review_create)
        
        assert isinstance(result, ReviewResponse)
        assert result.rating == mock_review.rating
        mock_user_dao.user_exists.assert_called_once_with(sample_review_create.user_id)
        mock_validator.product_exists.assert_called_once_with("product123")
        mock_review_dao.create_review.assert_called_once()
        mock_metrics_dao.create_metrics.assert_called_once()

    @pytest.mark.asyncio
    @patch('services.review_service.product_validator')
    async def test_create_review_invalid_user(
        self, mock_validator, review_service, mock_user_dao, sample_review_create
    ):
        """Test create_review with invalid user."""
        mock_user_dao.user_exists = Mock(return_value=False)
        
        with pytest.raises(ValidationException, match="Invalid user ID"):
            await review_service.create_review("product123", sample_review_create)
        
        mock_user_dao.user_exists.assert_called_once_with(sample_review_create.user_id)

    @pytest.mark.asyncio
    @patch('services.review_service.product_validator')
    async def test_create_review_product_not_found(
        self, mock_validator, review_service, mock_user_dao, sample_review_create
    ):
        """Test create_review with non-existent product."""
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_validator.product_exists = AsyncMock(return_value=False)
        
        with pytest.raises(ValidationException, match="Product not found"):
            await review_service.create_review("product123", sample_review_create)

    @pytest.mark.asyncio
    @patch('services.review_service.product_validator')
    async def test_create_review_duplicate(
        self, mock_validator, review_service, mock_user_dao, mock_review_dao, sample_review_create, mock_review
    ):
        """Test create_review when user already reviewed."""
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_validator.product_exists = AsyncMock(return_value=True)
        mock_review_dao.get_by_user_and_product = Mock(return_value=mock_review)
        
        with pytest.raises(ValidationException, match="already reviewed"):
            await review_service.create_review("product123", sample_review_create)

    @pytest.mark.asyncio
    @patch('services.review_service.product_validator')
    async def test_create_review_exception(
        self, mock_validator, review_service, mock_user_dao, mock_review_dao, sample_review_create
    ):
        """Test create_review when exception occurs."""
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_validator.product_exists = AsyncMock(return_value=True)
        mock_review_dao.get_by_user_and_product = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to create review"):
            await review_service.create_review("product123", sample_review_create)


class TestGetReviewsByProduct:
    """Test get_reviews_by_product method."""

    @pytest.mark.asyncio
    async def test_get_reviews_by_product_success(
        self, review_service, mock_review_dao, mock_metrics_dao, mock_comment_dao, mock_review
    ):
        """Test successful retrieval of reviews."""
        mock_review_dao.get_reviews_by_product = Mock(return_value=[mock_review])
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=MagicMock(comments_count=0))
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.get_reviews_by_product("product123", page=1, limit=20)
        
        assert len(result) == 1
        assert isinstance(result[0], ReviewResponse)
        mock_review_dao.get_reviews_by_product.assert_called_once_with("product123", 20, 0)

    @pytest.mark.asyncio
    async def test_get_reviews_by_product_pagination(
        self, review_service, mock_review_dao, mock_metrics_dao, mock_comment_dao, mock_review
    ):
        """Test get_reviews_by_product with pagination."""
        mock_review_dao.get_reviews_by_product = Mock(return_value=[mock_review])
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=MagicMock(comments_count=0))
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.get_reviews_by_product("product123", page=2, limit=10)
        
        assert len(result) == 1
        mock_review_dao.get_reviews_by_product.assert_called_once_with("product123", 10, 10)

    @pytest.mark.asyncio
    async def test_get_reviews_by_product_exception(
        self, review_service, mock_review_dao
    ):
        """Test get_reviews_by_product when exception occurs."""
        mock_review_dao.get_reviews_by_product = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to retrieve reviews"):
            await review_service.get_reviews_by_product("product123")


class TestUpdateReview:
    """Test update_review method."""

    @pytest.mark.asyncio
    async def test_update_review_success(
        self, review_service, mock_review_dao, mock_metrics_dao, mock_comment_dao, mock_review
    ):
        """Test successful review update."""
        update_data = ReviewUpdate(rating=4, description="Updated description")
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_review_dao.update_review = Mock(return_value=mock_review)
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=MagicMock(comments_count=0))
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.update_review(str(mock_review.id), update_data)
        
        assert isinstance(result, ReviewResponse)
        mock_review_dao.get_review_with_user.assert_called_once()
        mock_review_dao.update_review.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_review_not_found(self, review_service, mock_review_dao):
        """Test update_review when review doesn't exist."""
        update_data = ReviewUpdate(rating=4)
        mock_review_dao.get_review_with_user = Mock(return_value=None)
        
        with pytest.raises(NotFoundException, match="Review"):
            await review_service.update_review("nonexistent_id", update_data)

    @pytest.mark.asyncio
    async def test_update_review_with_votes(
        self, review_service, mock_review_dao, mock_metrics_dao, mock_comment_dao, mock_review
    ):
        """Test update_review with vote updates."""
        update_data = ReviewUpdate(upvotes=10, downvotes=2)
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_review_dao.update_review = Mock(return_value=mock_review)
        mock_metrics_dao.update_votes = Mock()
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=MagicMock(comments_count=0))
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.update_review(str(mock_review.id), update_data)
        
        assert isinstance(result, ReviewResponse)
        mock_metrics_dao.update_votes.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_review_with_rating_event(
        self, review_service, mock_review_dao, mock_metrics_dao, mock_comment_dao, mock_event_bus, mock_review
    ):
        """Test update_review emits event when rating changes."""
        update_data = ReviewUpdate(rating=3)
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_review_dao.update_review = Mock(return_value=mock_review)
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=MagicMock(comments_count=0))
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.update_review(str(mock_review.id), update_data)
        
        assert isinstance(result, ReviewResponse)
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_review_exception(
        self, review_service, mock_review_dao, mock_review
    ):
        """Test update_review when exception occurs."""
        update_data = ReviewUpdate(rating=4)
        mock_review_dao.get_review_with_user = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to update review"):
            await review_service.update_review(str(mock_review.id), update_data)


class TestDeleteReview:
    """Test delete_review method."""

    @pytest.mark.asyncio
    async def test_delete_review_success(
        self, review_service, mock_review_dao, mock_metrics_dao, mock_event_bus, mock_review
    ):
        """Test successful review deletion."""
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_metrics_dao.delete_metrics_by_review_id = Mock()
        mock_review_dao.delete = Mock()
        
        result = await review_service.delete_review(str(mock_review.id))
        
        assert result is True
        mock_review_dao.delete.assert_called_once()
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_review_not_found(self, review_service, mock_review_dao):
        """Test delete_review when review doesn't exist."""
        mock_review_dao.get_review_with_user = Mock(return_value=None)
        
        with pytest.raises(NotFoundException, match="Review"):
            await review_service.delete_review("nonexistent_id")

    @pytest.mark.asyncio
    async def test_delete_review_exception(
        self, review_service, mock_review_dao, mock_review
    ):
        """Test delete_review when exception occurs."""
        mock_review_dao.get_review_with_user = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to delete review"):
            await review_service.delete_review(str(mock_review.id))


class TestGetReviewResponse:
    """Test get_review_response method."""

    @pytest.mark.asyncio
    async def test_get_review_response_success(
        self, review_service, mock_metrics_dao, mock_comment_dao, mock_review
    ):
        """Test successful review response creation."""
        metrics = MagicMock()
        metrics.comments_count = 5
        metrics.upvotes = 10
        metrics.downvotes = 2
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=metrics)
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.get_review_response(mock_review)
        
        assert isinstance(result, ReviewResponse)
        assert result.id == str(mock_review.id)
        assert result.rating == mock_review.rating
        assert result.upvotes == 10
        assert result.downvotes == 2
        assert result.comments.total == 5

    @pytest.mark.asyncio
    async def test_get_review_response_with_comments(
        self, review_service, mock_metrics_dao, mock_comment_dao, mock_review
    ):
        """Test get_review_response with comments."""
        metrics = MagicMock()
        metrics.comments_count = 5
        metrics.upvotes = 0
        metrics.downvotes = 0
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=metrics)
        
        comment = MagicMock()
        comment.id = uuid4()
        comment.user = MagicMock()
        comment.user.id = uuid4()
        comment.user.name = "Commenter"
        comment.user.profile = "http://example.com/commenter.jpg"
        comment.description = "Nice review"
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[comment])
        
        result = await review_service.get_review_response(mock_review)
        
        assert result.comments.total == 5
        assert len(result.comments.data) == 1
        assert result.comments.data[0].description == "Nice review"

    @pytest.mark.asyncio
    async def test_get_review_response_no_metrics(
        self, review_service, mock_metrics_dao, mock_comment_dao, mock_review
    ):
        """Test get_review_response when metrics don't exist."""
        mock_metrics_dao.get_metrics_by_review = Mock(return_value=None)
        mock_comment_dao.get_recent_comments_by_review = Mock(return_value=[])
        
        result = await review_service.get_review_response(mock_review)
        
        assert result.upvotes == 0
        assert result.downvotes == 0
        assert result.comments.total == 0

    @pytest.mark.asyncio
    async def test_get_review_response_exception(
        self, review_service, mock_metrics_dao, mock_review
    ):
        """Test get_review_response when exception occurs."""
        mock_metrics_dao.get_metrics_by_review = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to format review response"):
            await review_service.get_review_response(mock_review)


class TestEventEmission:
    """Test event emission methods."""

    def test_emit_review_created_event(self, review_service, mock_event_bus):
        """Test ReviewCreated event emission."""
        review_service._emit_review_created_event(
            product_id="product123",
            review_id="review123",
            user_id="user123",
            rating=5
        )
        
        mock_event_bus.publish.assert_called_once()
        call_args = mock_event_bus.publish.call_args[0][0]
        assert isinstance(call_args, ReviewCreated)
        assert call_args.product_id == "product123"
        assert call_args.review_id == "review123"
        assert call_args.user_id == "user123"
        assert call_args.rating == 5

    def test_emit_review_created_event_no_event_bus(self):
        """Test ReviewCreated event emission when event_bus is None."""
        service = ReviewService(event_bus=None)
        service._emit_review_created_event(
            product_id="product123",
            review_id="review123",
            user_id="user123",
            rating=5
        )

    def test_emit_review_updated_event(self, review_service, mock_event_bus):
        """Test ReviewUpdated event emission."""
        review_service._emit_review_updated_event(
            product_id="product123",
            review_id="review123",
            rating=4
        )
        
        mock_event_bus.publish.assert_called_once()

    def test_emit_review_deleted_event(self, review_service, mock_event_bus):
        """Test ReviewDeleted event emission."""
        review_service._emit_review_deleted_event(
            product_id="product123",
            review_id="review123"
        )
        
        mock_event_bus.publish.assert_called_once()

