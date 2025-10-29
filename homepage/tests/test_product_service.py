"""Unit tests for ProductService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from services.product_service import ProductService, ServiceException, NotFoundException
from api.schemas import ProductCreate, ProductUpdate, ProductResponse
from db.models import ProductInDB


@pytest.fixture
def mock_product_dao():
    """Mock ProductDAO."""
    return AsyncMock()


@pytest.fixture
def mock_search_dao():
    """Mock SearchDAO."""
    return AsyncMock()


@pytest.fixture
def product_service(mock_product_dao, mock_search_dao):
    """Create ProductService instance with mocked DAOs."""
    return ProductService(product_dao=mock_product_dao, search_dao=mock_search_dao)


@pytest.fixture
def sample_product_in_db():
    """Sample ProductInDB object."""
    product_id = ObjectId()
    return ProductInDB(
        id=product_id,
        name="Test App",
        description="Test Description",
        developer="Test Developer",
        category="Games",
        price=9.99,
        version="1.0.0",
        rating=4.5,
        download_count=1000,
        icon_url="http://example.com/icon.png",
        screenshots=["http://example.com/screenshot1.png"],
        tags=["game", "fun"],
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_product_create():
    """Sample ProductCreate object."""
    return ProductCreate(
        name="Test App",
        description="Test Description",
        developer="Test Developer",
        category="Games",
        price=9.99,
        version="1.0.0",
        rating=4.5,
        download_count=1000,
        icon_url="http://example.com/icon.png",
        screenshots=["http://example.com/screenshot1.png"],
        tags=["game", "fun"]
    )


class TestProductServiceInit:
    """Test ProductService initialization."""

    def test_init_with_none_product_dao_raises_error(self, mock_search_dao):
        """Test that initializing with None product_dao raises ValueError."""
        with pytest.raises(ValueError, match="ProductDAO and SearchDAO must be provided"):
            ProductService(product_dao=None, search_dao=mock_search_dao)

    def test_init_with_none_search_dao_raises_error(self, mock_product_dao):
        """Test that initializing with None search_dao raises ValueError."""
        with pytest.raises(ValueError, match="ProductDAO and SearchDAO must be provided"):
            ProductService(product_dao=mock_product_dao, search_dao=None)

    def test_init_success(self, mock_product_dao, mock_search_dao):
        """Test successful initialization."""
        service = ProductService(product_dao=mock_product_dao, search_dao=mock_search_dao)
        assert service.product_dao == mock_product_dao
        assert service.search_dao == mock_search_dao


class TestConvertToResponse:
    """Test _convert_to_response method."""

    def test_convert_to_response(self, product_service, sample_product_in_db):
        """Test converting ProductInDB to ProductResponse."""
        result = product_service._convert_to_response(sample_product_in_db)
        
        assert isinstance(result, ProductResponse)
        assert result.id == str(sample_product_in_db.id)
        assert result.name == sample_product_in_db.name
        assert result.description == sample_product_in_db.description
        assert result.developer == sample_product_in_db.developer
        assert result.category == sample_product_in_db.category
        assert result.price == sample_product_in_db.price
        assert result.version == sample_product_in_db.version
        assert result.rating == sample_product_in_db.rating
        assert result.download_count == sample_product_in_db.download_count
        assert result.icon_url == sample_product_in_db.icon_url
        assert result.screenshots == sample_product_in_db.screenshots
        assert result.tags == sample_product_in_db.tags
        assert result.created_at == sample_product_in_db.created_at
        assert result.updated_at == sample_product_in_db.updated_at


class TestCreateProduct:
    """Test create_product method."""

    @pytest.mark.asyncio
    async def test_create_product_success(
        self, product_service, mock_product_dao, mock_search_dao, 
        sample_product_create, sample_product_in_db
    ):
        """Test successful product creation."""
        mock_product_dao.create_product = AsyncMock(return_value=sample_product_in_db)
        mock_search_dao.index_product = AsyncMock()
        
        result = await product_service.create_product(sample_product_create)
        
        assert isinstance(result, ProductResponse)
        assert result.id == str(sample_product_in_db.id)
        assert result.name == sample_product_in_db.name
        mock_product_dao.create_product.assert_called_once_with(sample_product_create)
        mock_search_dao.index_product.assert_called_once_with(sample_product_in_db)

    @pytest.mark.asyncio
    async def test_create_product_dao_exception(
        self, product_service, mock_product_dao, mock_search_dao, sample_product_create
    ):
        """Test create_product when DAO raises exception."""
        mock_product_dao.create_product = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to create product"):
            await product_service.create_product(sample_product_create)
        
        mock_search_dao.index_product.assert_not_called()


class TestGetProduct:
    """Test get_product method."""

    @pytest.mark.asyncio
    async def test_get_product_success(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test successful product retrieval."""
        mock_product_dao.get_product = AsyncMock(return_value=sample_product_in_db)
        
        result = await product_service.get_product(str(sample_product_in_db.id))
        
        assert isinstance(result, ProductResponse)
        assert result.id == str(sample_product_in_db.id)
        mock_product_dao.get_product.assert_called_once_with(str(sample_product_in_db.id))

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, product_service, mock_product_dao):
        """Test get_product when product doesn't exist."""
        mock_product_dao.get_product = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundException, match="Product"):
            await product_service.get_product("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_product_dao_exception(self, product_service, mock_product_dao):
        """Test get_product when DAO raises exception."""
        mock_product_dao.get_product = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to retrieve product"):
            await product_service.get_product("test_id")

    @pytest.mark.asyncio
    async def test_get_product_not_found_exception_re_raised(
        self, product_service, mock_product_dao
    ):
        """Test that NotFoundException is re-raised."""
        mock_product_dao.get_product = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundException):
            await product_service.get_product("test_id")


class TestListProducts:
    """Test list_products method."""

    @pytest.mark.asyncio
    async def test_list_products_success(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test successful product listing."""
        products = [sample_product_in_db]
        mock_product_dao.list_products = AsyncMock(return_value=(products, 1))
        
        result = await product_service.list_products(page=1, page_size=20)
        
        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 1
        assert len(result.products) == 1
        assert result.products[0].id == str(sample_product_in_db.id)
        mock_product_dao.list_products.assert_called_once_with(skip=0, limit=20, category=None)

    @pytest.mark.asyncio
    async def test_list_products_with_category(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test list_products with category filter."""
        products = [sample_product_in_db]
        mock_product_dao.list_products = AsyncMock(return_value=(products, 1))
        
        result = await product_service.list_products(page=1, page_size=20, category="Games")
        
        assert result.total == 1
        mock_product_dao.list_products.assert_called_once_with(skip=0, limit=20, category="Games")

    @pytest.mark.asyncio
    async def test_list_products_pagination(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test list_products pagination."""
        products = [sample_product_in_db]
        mock_product_dao.list_products = AsyncMock(return_value=(products, 25))
        
        result = await product_service.list_products(page=2, page_size=10)
        
        assert result.total == 25
        assert result.page == 2
        assert result.page_size == 10
        assert result.total_pages == 3
        mock_product_dao.list_products.assert_called_once_with(skip=10, limit=10, category=None)

    @pytest.mark.asyncio
    async def test_list_products_empty_total(self, product_service, mock_product_dao):
        """Test list_products with zero total."""
        mock_product_dao.list_products = AsyncMock(return_value=([], 0))
        
        result = await product_service.list_products(page=1, page_size=20)
        
        assert result.total == 0
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_list_products_dao_exception(self, product_service, mock_product_dao):
        """Test list_products when DAO raises exception."""
        mock_product_dao.list_products = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to retrieve products"):
            await product_service.list_products(page=1, page_size=20)


class TestUpdateProduct:
    """Test update_product method."""

    @pytest.mark.asyncio
    async def test_update_product_success(
        self, product_service, mock_product_dao, mock_search_dao, 
        sample_product_in_db
    ):
        """Test successful product update."""
        update_data = ProductUpdate(name="Updated Name")
        mock_product_dao.update_product = AsyncMock(return_value=sample_product_in_db)
        mock_search_dao.index_product = AsyncMock()
        
        result = await product_service.update_product(str(sample_product_in_db.id), update_data)
        
        assert isinstance(result, ProductResponse)
        assert result.id == str(sample_product_in_db.id)
        mock_product_dao.update_product.assert_called_once()
        mock_search_dao.index_product.assert_called_once_with(sample_product_in_db)

    @pytest.mark.asyncio
    async def test_update_product_not_found(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test update_product when product doesn't exist."""
        update_data = ProductUpdate(name="Updated Name")
        mock_product_dao.update_product = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundException, match="Product"):
            await product_service.update_product(str(sample_product_in_db.id), update_data)

    @pytest.mark.asyncio
    async def test_update_product_dao_exception(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test update_product when DAO raises exception."""
        update_data = ProductUpdate(name="Updated Name")
        mock_product_dao.update_product = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to update product"):
            await product_service.update_product(str(sample_product_in_db.id), update_data)

    @pytest.mark.asyncio
    async def test_update_product_not_found_exception_re_raised(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test that NotFoundException is re-raised."""
        update_data = ProductUpdate(name="Updated Name")
        mock_product_dao.update_product = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundException):
            await product_service.update_product(str(sample_product_in_db.id), update_data)


class TestDeleteProduct:
    """Test delete_product method."""

    @pytest.mark.asyncio
    async def test_delete_product_success(
        self, product_service, mock_product_dao, mock_search_dao, sample_product_in_db
    ):
        """Test successful product deletion."""
        mock_product_dao.get_product = AsyncMock(return_value=sample_product_in_db)
        mock_product_dao.delete_product = AsyncMock(return_value=True)
        mock_search_dao.delete_product = AsyncMock()
        
        result = await product_service.delete_product(str(sample_product_in_db.id))
        
        assert result is True
        mock_product_dao.get_product.assert_called_once()
        mock_product_dao.delete_product.assert_called_once()
        mock_search_dao.delete_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, product_service, mock_product_dao):
        """Test delete_product when product doesn't exist."""
        mock_product_dao.get_product = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundException, match="Product"):
            await product_service.delete_product("nonexistent_id")

    @pytest.mark.asyncio
    async def test_delete_product_delete_fails(
        self, product_service, mock_product_dao, mock_search_dao, sample_product_in_db
    ):
        """Test delete_product when delete operation fails."""
        mock_product_dao.get_product = AsyncMock(return_value=sample_product_in_db)
        mock_product_dao.delete_product = AsyncMock(return_value=False)
        
        with pytest.raises(ServiceException, match="Failed to delete product"):
            await product_service.delete_product(str(sample_product_in_db.id))
        
        mock_search_dao.delete_product.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_product_dao_exception(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test delete_product when DAO raises exception."""
        mock_product_dao.get_product = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(ServiceException, match="Failed to delete product"):
            await product_service.delete_product(str(sample_product_in_db.id))

    @pytest.mark.asyncio
    async def test_delete_product_exceptions_re_raised(
        self, product_service, mock_product_dao, sample_product_in_db
    ):
        """Test that NotFoundException and ServiceException are re-raised."""
        mock_product_dao.get_product = AsyncMock(return_value=None)
        
        with pytest.raises(NotFoundException):
            await product_service.delete_product(str(sample_product_in_db.id))


class TestSearchProducts:
    """Test search_products method."""

    @pytest.mark.asyncio
    async def test_search_products_success(
        self, product_service, mock_product_dao, mock_search_dao, sample_product_in_db
    ):
        """Test successful product search."""
        search_results = [{"id": str(sample_product_in_db.id)}]
        mock_search_dao.search_products = AsyncMock(return_value=(search_results, 1, 50))
        mock_product_dao.get_product = AsyncMock(return_value=sample_product_in_db)
        
        result = await product_service.search_products("test query")
        
        assert result.total == 1
        assert result.query == "test query"
        assert result.took == 50
        assert len(result.products) == 1
        assert result.products[0].id == str(sample_product_in_db.id)
        mock_search_dao.search_products.assert_called_once()
        mock_product_dao.get_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_products_with_category(
        self, product_service, mock_product_dao, mock_search_dao, sample_product_in_db
    ):
        """Test search_products with category filter."""
        search_results = [{"id": str(sample_product_in_db.id)}]
        mock_search_dao.search_products = AsyncMock(return_value=(search_results, 1, 50))
        mock_product_dao.get_product = AsyncMock(return_value=sample_product_in_db)
        
        result = await product_service.search_products("test query", category="Games")
        
        assert result.total == 1
        mock_search_dao.search_products.assert_called_once()
        call_kwargs = mock_search_dao.search_products.call_args[1]
        assert call_kwargs["category"] == "Games"

    @pytest.mark.asyncio
    async def test_search_products_no_product_found(
        self, product_service, mock_product_dao, mock_search_dao
    ):
        """Test search_products when product not found in database."""
        search_results = [{"id": "nonexistent_id"}]
        mock_search_dao.search_products = AsyncMock(return_value=(search_results, 1, 50))
        mock_product_dao.get_product = AsyncMock(return_value=None)
        
        result = await product_service.search_products("test query")
        
        assert result.total == 1
        assert len(result.products) == 0

    @pytest.mark.asyncio
    async def test_search_products_pagination(
        self, product_service, mock_product_dao, mock_search_dao, sample_product_in_db
    ):
        """Test search_products pagination."""
        search_results = [{"id": str(sample_product_in_db.id)}]
        mock_search_dao.search_products = AsyncMock(return_value=(search_results, 10, 50))
        mock_product_dao.get_product = AsyncMock(return_value=sample_product_in_db)
        
        result = await product_service.search_products("test query", page=2, page_size=5)
        
        assert result.total == 10
        call_kwargs = mock_search_dao.search_products.call_args[1]
        assert call_kwargs["skip"] == 5
        assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_products_dao_exception(
        self, product_service, mock_product_dao, mock_search_dao
    ):
        """Test search_products when DAO raises exception."""
        mock_search_dao.search_products = AsyncMock(side_effect=Exception("Search error"))
        
        with pytest.raises(ServiceException, match="Search failed"):
            await product_service.search_products("test query")

