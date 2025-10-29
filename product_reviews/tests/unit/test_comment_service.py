"""Unit tests for CommentService."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4

from services.comment_service import CommentService
from services.base_service import ServiceException, ValidationException, NotFoundException
from api.schemas import CommentCreate, CommentResponse


@pytest.fixture
def mock_comment_dao():
    """Mock CommentDAO."""
    return Mock()


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
def comment_service(mock_comment_dao, mock_review_dao, mock_user_dao, mock_metrics_dao):
    """Create CommentService instance with mocked DAOs."""
    return CommentService(
        comment_dao=mock_comment_dao,
        review_dao=mock_review_dao,
        user_dao=mock_user_dao,
        metrics_dao=mock_metrics_dao
    )


@pytest.fixture
def mock_review():
    """Mock Review object."""
    review = MagicMock()
    review.id = uuid4()
    review.product_id = "product123"
    review.user_id = str(uuid4())
    review.status = "active"
    return review


@pytest.fixture
def mock_comment():
    """Mock Comment object."""
    user_uuid = uuid4()
    comment = MagicMock()
    comment.id = uuid4()
    comment.review_id = str(uuid4())
    comment.user_id = str(user_uuid)
    comment.description = "Great review!"
    comment.created_at = datetime.now(timezone.utc)
    comment.user = MagicMock()
    comment.user.id = user_uuid
    comment.user.name = "Commenter"
    comment.user.profile = "http://example.com/profile.jpg"
    return comment


@pytest.fixture
def sample_comment_create():
    """Sample CommentCreate object."""
    return CommentCreate(
        user_id=str(uuid4()),
        description="Great review!"
    )


class TestCommentServiceInit:
    """Test CommentService initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default DAOs."""
        service = CommentService()
        assert service.comment_dao is not None
        assert service.review_dao is not None
        assert service.metrics_dao is not None

    def test_init_with_custom_daos(self, mock_comment_dao, mock_review_dao, mock_user_dao, mock_metrics_dao):
        """Test initialization with custom DAOs."""
        service = CommentService(
            comment_dao=mock_comment_dao,
            review_dao=mock_review_dao,
            user_dao=mock_user_dao,
            metrics_dao=mock_metrics_dao
        )
        assert service.comment_dao == mock_comment_dao
        assert service.review_dao == mock_review_dao
        assert service.metrics_dao == mock_metrics_dao


class TestCreateComment:
    """Test create_comment method."""

    @pytest.mark.asyncio
    async def test_create_comment_success(
        self, comment_service, mock_user_dao, mock_review_dao, 
        mock_comment_dao, mock_metrics_dao, sample_comment_create, mock_review, mock_comment
    ):
        """Test successful comment creation."""
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_comment_dao.create_comment = Mock(return_value=mock_comment)
        mock_metrics_dao.increment_comments_count = Mock()
        
        result = await comment_service.create_comment("review123", sample_comment_create)
        
        assert result is True
        mock_user_dao.user_exists.assert_called_once_with(sample_comment_create.user_id)
        mock_review_dao.get_review_with_user.assert_called_once_with("review123")
        mock_comment_dao.create_comment.assert_called_once()
        mock_metrics_dao.increment_comments_count.assert_called_once_with("review123")

    @pytest.mark.asyncio
    async def test_create_comment_invalid_user(
        self, comment_service, mock_user_dao, sample_comment_create
    ):
        """Test create_comment with invalid user."""
        mock_user_dao.user_exists = Mock(return_value=False)
        
        with pytest.raises(ValidationException, match="Invalid user ID"):
            await comment_service.create_comment("review123", sample_comment_create)

    @pytest.mark.asyncio
    async def test_create_comment_review_not_found(
        self, comment_service, mock_user_dao, mock_review_dao, sample_comment_create
    ):
        """Test create_comment with non-existent review."""
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_review_dao.get_review_with_user = Mock(return_value=None)
        
        with pytest.raises(NotFoundException, match="Review"):
            await comment_service.create_comment("nonexistent_id", sample_comment_create)

    @pytest.mark.asyncio
    async def test_create_comment_inactive_review(
        self, comment_service, mock_user_dao, mock_review_dao, sample_comment_create, mock_review
    ):
        """Test create_comment on inactive review."""
        mock_review.status = "inactive"
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        
        with pytest.raises(ValidationException, match="inactive review"):
            await comment_service.create_comment("review123", sample_comment_create)

    @pytest.mark.asyncio
    async def test_create_comment_exception(
        self, comment_service, mock_user_dao, mock_review_dao, sample_comment_create, mock_review
    ):
        """Test create_comment when exception occurs."""
        mock_user_dao.user_exists = Mock(return_value=True)
        mock_review_dao.get_review_with_user = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to create comment"):
            await comment_service.create_comment("review123", sample_comment_create)


class TestGetCommentsByReview:
    """Test get_comments_by_review method."""

    @pytest.mark.asyncio
    async def test_get_comments_by_review_success(
        self, comment_service, mock_review_dao, mock_comment_dao, mock_review, mock_comment
    ):
        """Test successful comment retrieval."""
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_comment_dao.get_comments_by_review = Mock(return_value=[mock_comment])
        
        result = await comment_service.get_comments_by_review("review123", page=1, limit=20)
        
        assert len(result) == 1
        assert isinstance(result[0], CommentResponse)
        assert result[0].description == mock_comment.description
        mock_review_dao.get_review_with_user.assert_called_once_with("review123")
        mock_comment_dao.get_comments_by_review.assert_called_once_with("review123", 20, 0)

    @pytest.mark.asyncio
    async def test_get_comments_by_review_pagination(
        self, comment_service, mock_review_dao, mock_comment_dao, mock_review, mock_comment
    ):
        """Test get_comments_by_review with pagination."""
        mock_review_dao.get_review_with_user = Mock(return_value=mock_review)
        mock_comment_dao.get_comments_by_review = Mock(return_value=[mock_comment])
        
        result = await comment_service.get_comments_by_review("review123", page=2, limit=10)
        
        assert len(result) == 1
        mock_comment_dao.get_comments_by_review.assert_called_once_with("review123", 10, 10)

    @pytest.mark.asyncio
    async def test_get_comments_by_review_not_found(
        self, comment_service, mock_review_dao
    ):
        """Test get_comments_by_review when review doesn't exist."""
        mock_review_dao.get_review_with_user = Mock(return_value=None)
        
        with pytest.raises(NotFoundException, match="Review"):
            await comment_service.get_comments_by_review("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_comments_by_review_exception(
        self, comment_service, mock_review_dao, mock_review
    ):
        """Test get_comments_by_review when exception occurs."""
        mock_review_dao.get_review_with_user = Mock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to retrieve comments"):
            await comment_service.get_comments_by_review("review123")


class TestGetCommentResponse:
    """Test get_comment_response method."""

    @pytest.mark.asyncio
    async def test_get_comment_response_success(
        self, comment_service, mock_comment
    ):
        """Test successful comment response creation."""
        result = await comment_service.get_comment_response(mock_comment)
        
        assert isinstance(result, CommentResponse)
        assert result.id == str(mock_comment.id)
        assert result.description == mock_comment.description
        assert result.user_details.id == str(mock_comment.user.id)
        assert result.user_details.name == mock_comment.user.name
        assert result.user_details.profile == mock_comment.user.profile
        assert result.created_at == mock_comment.created_at

    @pytest.mark.asyncio
    async def test_get_comment_response_exception(
        self, comment_service, mock_comment
    ):
        """Test get_comment_response when exception occurs."""
        mock_comment.user = None  # This will cause an error when accessing user attributes
        
        with pytest.raises(ServiceException, match="Failed to format comment response"):
            await comment_service.get_comment_response(mock_comment)

