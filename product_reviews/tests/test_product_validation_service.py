"""Unit tests for ProductValidationService."""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from bson import ObjectId
from bson.errors import InvalidId

from services.product_validation_service import ProductValidationService


@pytest.fixture
def validation_service():
    """Create ProductValidationService instance."""
    return ProductValidationService()


class TestProductValidationServiceInit:
    """Test ProductValidationService initialization."""

    def test_init_defaults(self, validation_service):
        """Test initialization with default values."""
        assert validation_service.client is None
        assert validation_service.database is None
        assert validation_service.collection is None
        assert validation_service.mongodb_url is not None
        assert validation_service.mongodb_database is not None
        assert validation_service.mongodb_collection is not None

    @patch.dict('os.environ', {
        'HOMEPAGE_MONGODB_URL': 'mongodb://custom:27017',
        'HOMEPAGE_MONGODB_DATABASE': 'custom_db',
        'HOMEPAGE_MONGODB_COLLECTION': 'custom_collection'
    })
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        service = ProductValidationService()
        assert service.mongodb_url == 'mongodb://custom:27017'
        assert service.mongodb_database == 'custom_db'
        assert service.mongodb_collection == 'custom_collection'


class TestConnect:
    """Test connect method."""

    @pytest.mark.asyncio
    @patch('services.product_validation_service.AsyncIOMotorClient')
    async def test_connect_success(self, mock_client_class, validation_service):
        """Test successful connection."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the database and collection access
        mock_database = MagicMock()
        mock_collection = MagicMock()
        mock_client.__getitem__ = Mock(return_value=mock_database)
        mock_database.__getitem__ = Mock(return_value=mock_collection)
        mock_client.admin.command = AsyncMock()
        
        await validation_service.connect()
        
        assert validation_service.client is not None
        assert validation_service.database is not None
        assert validation_service.collection is not None
        mock_client.admin.command.assert_called_once_with('ping')

    @pytest.mark.asyncio
    @patch('services.product_validation_service.AsyncIOMotorClient')
    async def test_connect_failure(self, mock_client_class, validation_service):
        """Test connection failure."""
        mock_client_class.side_effect = Exception("Connection error")
        
        await validation_service.connect()
        
        assert validation_service.client is None
        assert validation_service.database is None
        assert validation_service.collection is None


class TestDisconnect:
    """Test disconnect method."""

    @pytest.mark.asyncio
    async def test_disconnect_with_client(self, validation_service):
        """Test disconnect when client exists."""
        mock_client = Mock()
        mock_client.close = Mock()
        validation_service.client = mock_client
        
        await validation_service.disconnect()
        
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_without_client(self, validation_service):
        """Test disconnect when client is None."""
        validation_service.client = None
        
        await validation_service.disconnect()
        
        # Should not raise exception


class TestProductExists:
    """Test product_exists method."""

    @pytest.mark.asyncio
    async def test_product_exists_success(self, validation_service):
        """Test product_exists when product exists."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value={"_id": ObjectId(), "name": "Product"})
        validation_service.collection = mock_collection
        product_id = str(ObjectId())
        
        result = await validation_service.product_exists(product_id)
        
        assert result is True
        mock_collection.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_product_exists_not_found(self, validation_service):
        """Test product_exists when product doesn't exist."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        validation_service.collection = mock_collection
        product_id = str(ObjectId())
        
        result = await validation_service.product_exists(product_id)
        
        assert result is False
        mock_collection.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_product_exists_no_collection(self, validation_service):
        """Test product_exists when collection is not connected."""
        validation_service.collection = None
        product_id = str(ObjectId())
        
        result = await validation_service.product_exists(product_id)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_product_exists_invalid_object_id(self, validation_service):
        """Test product_exists with invalid ObjectId format."""
        mock_collection = AsyncMock()
        validation_service.collection = mock_collection
        
        result = await validation_service.product_exists("invalid_id")
        
        assert result is False
        mock_collection.find_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_product_exists_exception(self, validation_service):
        """Test product_exists when exception occurs."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(side_effect=Exception("Database error"))
        validation_service.collection = mock_collection
        product_id = str(ObjectId())
        
        result = await validation_service.product_exists(product_id)
        
        assert result is False


class TestIsConnected:
    """Test is_connected method."""

    def test_is_connected_true(self, validation_service):
        """Test is_connected when both client and collection exist."""
        validation_service.client = Mock()
        validation_service.collection = Mock()
        
        assert validation_service.is_connected() is True

    def test_is_connected_no_client(self, validation_service):
        """Test is_connected when client is None."""
        validation_service.client = None
        validation_service.collection = Mock()
        
        assert validation_service.is_connected() is False

    def test_is_connected_no_collection(self, validation_service):
        """Test is_connected when collection is None."""
        validation_service.client = Mock()
        validation_service.collection = None
        
        assert validation_service.is_connected() is False

    def test_is_connected_both_none(self, validation_service):
        """Test is_connected when both are None."""
        validation_service.client = None
        validation_service.collection = None
        
        assert validation_service.is_connected() is False

