"""Pytest configuration and fixtures for integration tests."""

import os
import pytest
import config
from pathlib import Path
from typing import AsyncGenerator, Dict
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Settings
from db.manager import DatabaseManager
from services.product_service import ProductService
from api.routers import ProductRouter, AdminProductRouter

# Elasticsearch index mapping for test data
ELASTICSEARCH_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "name": {"type": "text", "analyzer": "standard", "fields": {"keyword": {"type": "keyword"}}},
            "description": {"type": "text", "analyzer": "standard"},
            "developer": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "category": {"type": "keyword"},
            "price": {"type": "float"},
            "version": {"type": "keyword"},
            "rating": {"type": "float"},
            "download_count": {"type": "long"},
            "tags": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    }
}


def _create_test_settings() -> Settings:
    """Create test settings instance from .env.test file or environment variables."""
    test_env_file = Path(__file__).parent.parent.parent / ".env.test"
    
    if test_env_file.exists():
        return Settings(env_file=str(test_env_file))
    
    test_env_vars = {
        "MONGODB_URL": os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017"),
        "MONGODB_DATABASE": os.getenv("TEST_MONGODB_DATABASE", "appstore_test"),
        "MONGODB_COLLECTION": os.getenv("TEST_MONGODB_COLLECTION", "products_test"),
        "ELASTICSEARCH_URL": os.getenv("TEST_ELASTICSEARCH_URL", "http://localhost:9200"),
        "ELASTICSEARCH_INDEX": os.getenv("TEST_ELASTICSEARCH_INDEX", "products_test"),
    }
    
    # Temporarily set environment variables, create settings, then restore
    original_env = {}
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        return Settings()
    finally:
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture(scope="session", autouse=True)
def override_settings():
    """Override global settings with test settings before any test runs."""
    # Create test settings instance - this will read .env.test or use test defaults
    test_settings = _create_test_settings()
    
    # Verify test database is different from main
    assert test_settings.mongodb_database != config.settings.mongodb_database, \
        f"Test database '{test_settings.mongodb_database}' must be different from main database '{config.settings.mongodb_database}'"
    
    original_settings = config.settings
    config.settings = test_settings
    
    yield
    
    config.settings = original_settings


async def _cleanup_databases(manager: DatabaseManager):
    """Clean up test databases (MongoDB collections and Elasticsearch indices)."""
    try:
        # Clean MongoDB collection
        if manager.mongodb_collection is not None:
            # Safety check: ensure we're cleaning the test database
            db_name = manager.mongodb_collection.database.name
            if not db_name.endswith("_test"):
                raise RuntimeError(
                    f"CRITICAL: Attempted to clean production database '{db_name}'. "
                    f"Only test databases (ending with '_test') should be cleaned."
                )
            await manager.mongodb_collection.delete_many({})
        
        # Clean and recreate Elasticsearch index
        if manager.elasticsearch_client is not None and manager.search_dao is not None:
            es_index = manager.search_dao.index_name
            if es_index:
                try:
                    if await manager.elasticsearch_client.indices.exists(index=es_index):
                        await manager.elasticsearch_client.indices.delete(index=es_index)
                    
                    await manager.elasticsearch_client.indices.create(
                        index=es_index,
                        body=ELASTICSEARCH_INDEX_MAPPING
                    )
                except Exception as e:
                    print(f"Error cleaning up/recreating Elasticsearch index: {e}")
    except Exception as e:
        print(f"Error in cleanup: {e}")


@pytest.fixture(scope="function")
async def test_db_manager(override_settings) -> AsyncGenerator[DatabaseManager, None]:
    """Create and initialize test database manager with cleanup."""
    # Ensure we're using test settings
    from config import settings
    assert settings.mongodb_database.endswith("_test"), \
        f"Using wrong database: '{settings.mongodb_database}' - must end with '_test'"
    
    manager = DatabaseManager()
    await manager.connect()
    
    # Double-check we're connected to test database
    connected_db = manager.mongodb_collection.database.name
    assert connected_db.endswith("_test"), \
        f"Connected to wrong database: '{connected_db}' - must end with '_test'"
    
    # Clean up before test to ensure fresh state
    await _cleanup_databases(manager)
    
    yield manager
    
    # Clean up after test
    try:
        await _cleanup_databases(manager)
        await manager.disconnect()
    except Exception as e:
        print(f"Error in test_db_manager teardown: {e}")


def create_test_app(db_manager: DatabaseManager) -> FastAPI:
    """Create and configure FastAPI app instance for testing."""
    # Access config.settings to ensure we get the patched test settings from override_settings fixture
    settings = config.settings
    
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description="API for App Store-like homepage functionality"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services and routers
    product_service = ProductService(
        product_dao=db_manager.product_dao,
        search_dao=db_manager.search_dao
    )
    
    product_router = ProductRouter(product_service=product_service)
    admin_product_router = AdminProductRouter(product_service=product_service)
    
    app.include_router(product_router.router)
    app.include_router(admin_product_router.router)
    
    # Add root and health check endpoints
    @app.get("/", response_model=Dict[str, str])
    async def root():
        return {
            "message": "Welcome to App Store Homepage API",
            "version": settings.app_version
        }
    
    @app.get("/health")
    async def health_check():
        mongodb_status = "connected" if db_manager.mongodb_client else "disconnected"
        elasticsearch_status = "connected" if db_manager.elasticsearch_client else "disconnected"
        overall_status = "healthy" if mongodb_status == "connected" else "degraded"
        
        return {
            "status": overall_status,
            "mongodb": mongodb_status,
            "elasticsearch": elasticsearch_status,
            "version": settings.app_version
        }
    
    return app


@pytest.fixture
async def client(test_db_manager) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP test client for API testing."""
    test_app = create_test_app(test_db_manager)
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
