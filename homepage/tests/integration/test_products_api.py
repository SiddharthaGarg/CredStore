"""Integration tests for Products API endpoints."""

import pytest
from httpx import AsyncClient
from bson import ObjectId

from api.schemas import ProductCreate, ProductResponse


@pytest.mark.asyncio
class TestCreateProduct:
    """Integration tests for creating products."""
    
    async def test_create_product_success(self, client: AsyncClient):
        """Test successful product creation."""
        product_data = {
            "name": "Test Product",
            "description": "A test product description",
            "developer": "Test Developer",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0",
            "rating": 4.5,
            "download_count": 1000,
            "icon_url": "http://example.com/icon.png",
            "screenshots": ["http://example.com/screenshot1.png"],
            "tags": ["game", "fun"]
        }
        
        response = await client.post("/admin/products", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == product_data["name"]
        assert data["description"] == product_data["description"]
        assert data["developer"] == product_data["developer"]
        assert data["category"] == product_data["category"]
        assert data["price"] == product_data["price"]
        assert data["version"] == product_data["version"]
        assert data["rating"] == product_data["rating"]
        assert data["download_count"] == product_data["download_count"]
        assert "created_at" in data
        assert "updated_at" in data


@pytest.mark.asyncio
class TestListProducts:
    """Integration tests for listing products."""
    
    async def test_list_products_success_empty(self, client: AsyncClient):
        """Test listing products when database is empty."""
        response = await client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert isinstance(data["products"], list)
        assert data["total"] == 0
        assert data["products"] == []
    
    async def test_list_products_success_with_data(
        self, client: AsyncClient
    ):
        """Test listing products with existing data."""
        product_data = {
            "name": "Test Product 1",
            "description": "First test product",
            "developer": "Developer 1",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0",
            "tags": ["game"]
        }
        
        create_response = await client.post("/admin/products", json=product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        response = await client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["products"]) >= 1
        assert any(p["id"] == created_product["id"] for p in data["products"])
    
    async def test_list_products_with_pagination(
        self, client: AsyncClient
    ):
        """Test listing products with pagination."""
        for i in range(3):
            product_data = {
                "name": f"Test Product {i+1}",
                "description": f"Test product {i+1}",
                "developer": "Test Developer",
                "category": "Games",
                "price": 9.99 + i,
                "version": "1.0.0"
            }
            await client.post("/admin/products", json=product_data)
        
        response = await client.get("/products?page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
    
    async def test_list_products_with_category_filter(
        self, client: AsyncClient
    ):
        """Test listing products filtered by category."""
        games_product = {
            "name": "Game Product",
            "description": "A game",
            "developer": "Game Dev",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0"
        }
        
        utility_product = {
            "name": "Utility Product",
            "description": "A utility",
            "developer": "Utility Dev",
            "category": "Utility",
            "price": 4.99,
            "version": "1.0.0"
        }
        
        await client.post("/admin/products", json=games_product)
        await client.post("/admin/products", json=utility_product)
        
        response = await client.get("/products?category=Games")
        
        assert response.status_code == 200
        data = response.json()
        assert all(p["category"] == "Games" for p in data["products"])


@pytest.mark.asyncio
class TestGetProduct:
    """Integration tests for getting a single product."""
    
    async def test_get_product_success(self, client: AsyncClient):
        """Test successfully getting a product by ID."""
        product_data = {
            "name": "Test Product",
            "description": "Test description",
            "developer": "Test Developer",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0"
        }
        
        create_response = await client.post("/admin/products", json=product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        product_id = created_product["id"]
        
        response = await client.get(f"/products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == product_data["name"]
        assert data["description"] == product_data["description"]
        assert data["developer"] == product_data["developer"]
        assert data["category"] == product_data["category"]
        assert data["price"] == product_data["price"]


@pytest.mark.asyncio
class TestUpdateProduct:
    """Integration tests for updating products."""
    
    async def test_update_product_success(self, client: AsyncClient):
        """Test successful product update."""
        product_data = {
            "name": "Original Product",
            "description": "Original description",
            "developer": "Original Developer",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0"
        }
        
        create_response = await client.post("/admin/products", json=product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        product_id = created_product["id"]
        
        update_data = {
            "name": "Updated Product",
            "description": "Updated description",
            "price": 14.99
        }
        
        response = await client.put(f"/admin/products/{product_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["price"] == update_data["price"]
        assert data["developer"] == product_data["developer"]
        assert data["category"] == product_data["category"]


@pytest.mark.asyncio
class TestDeleteProduct:
    """Integration tests for deleting products."""
    
    async def test_delete_product_success(self, client: AsyncClient):
        """Test successful product deletion."""
        product_data = {
            "name": "Product to Delete",
            "description": "This will be deleted",
            "developer": "Test Developer",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0"
        }
        
        create_response = await client.post("/admin/products", json=product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        product_id = created_product["id"]
        
        delete_response = await client.delete(f"/admin/products/{product_id}")
        
        assert delete_response.status_code == 200
        
        get_response = await client.get(f"/products/{product_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
class TestSearchProducts:
    """Integration tests for searching products."""
    
    async def test_search_products_success(self, client: AsyncClient):
        """Test successful product search."""
        product_data = {
            "name": "Amazing Game",
            "description": "An amazing game with great features",
            "developer": "Game Studios",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0",
            "tags": ["game", "action", "adventure"]
        }
        
        create_response = await client.post("/admin/products", json=product_data)
        assert create_response.status_code == 201
        
        import asyncio
        await asyncio.sleep(1)
        
        response = await client.get("/products/search?q=amazing")
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "query" in data
        assert "took" in data
        assert data["query"] == "amazing"
        assert isinstance(data["products"], list)
        assert len(data["products"]) >= 0
    
    async def test_search_products_with_category(
        self, client: AsyncClient
    ):
        """Test searching products with category filter."""
        games_product = {
            "name": "Action Game",
            "description": "An action-packed game",
            "developer": "Game Dev",
            "category": "Games",
            "price": 9.99,
            "version": "1.0.0"
        }
        
        await client.post("/admin/products", json=games_product)
        
        import asyncio
        await asyncio.sleep(1)
        
        response = await client.get("/products/search?q=action&category=Games")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "action"
        assert all(p["category"] == "Games" for p in data["products"])

