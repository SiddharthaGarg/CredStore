"""Pytest configuration and fixtures for integration tests."""

import os
import pytest
import config
from pathlib import Path
from typing import AsyncGenerator, Dict
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4

from config import Settings
from db.manager import DatabaseManager
from api.routers import reviews_router
from db.models import User
from services import product_validator
from db.models import Review, Comment, ReviewMetrics, User, database as db_module


def _create_test_settings() -> Settings:
    """Create test settings instance from .env.test file or environment variables."""
    test_env_file = Path(__file__).parent.parent.parent / ".env.test"
    
    if test_env_file.exists():
        return Settings(env_file=str(test_env_file))
    
    test_env_vars = {
        "DB_HOST": os.getenv("TEST_DB_HOST", "localhost"),
        "DB_PORT": os.getenv("TEST_DB_PORT", "5432"),
        "DB_NAME": os.getenv("TEST_DB_NAME", "product_reviews_test"),
        "DB_USER": os.getenv("TEST_DB_USER", "postgres"),
        "DB_PASSWORD": os.getenv("TEST_DB_PASSWORD", "password"),
    }
    
    original_env = {}
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        return Settings()
    finally:
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture(scope="session", autouse=True)
def override_settings():
    """Override global settings with test settings before any test runs."""
    test_settings = _create_test_settings()
    
    assert test_settings.db_name.endswith("_test"), \
        f"Test database '{test_settings.db_name}' must end with '_test'"
    assert test_settings.db_name != config.settings.db_name, \
        f"Test database '{test_settings.db_name}' must be different from main database '{config.settings.db_name}'"
    
    original_settings = config.settings
    config.settings = test_settings
    
    yield
    
    config.settings = original_settings

async def _cleanup_database(db_manager: DatabaseManager):
    """Clean up test database tables."""
    try:
        # Ensure database is connected before cleanup
        if db_module.is_closed():
            return
        
        # Delete in correct order (respecting foreign keys)
        ReviewMetrics.delete().execute()
        Comment.delete().execute()
        Review.delete().execute()
        User.delete().execute()
    except Exception as e:
        print(f"Error in cleanup: {e}")


@pytest.fixture(scope="function")
async def test_db_manager(override_settings) -> AsyncGenerator[DatabaseManager, None]:
    """Create and initialize test database manager with cleanup."""
    from config import settings as test_settings
    
    assert test_settings.db_name.endswith("_test"), \
        f"Using wrong database: '{test_settings.db_name}' - must end with '_test'"
    
    manager = DatabaseManager()
    await manager.connect()
    
    if db_module.is_closed():
        raise RuntimeError("Database connection is closed after manager.connect() succeeded")
    
    try:
        db_name = db_module.execute_sql("SELECT current_database()").fetchone()[0]
        assert db_name.endswith("_test"), \
            f"Connected to wrong database: '{db_name}' - must end with '_test'"
    except Exception as e:
        raise RuntimeError(f"Failed to verify database connection: {e}") from e
    
    # Clean up before test to ensure fresh state
    await _cleanup_database(manager)
    
    yield manager
    
    # Clean up after test
    try:
        await _cleanup_database(manager)
        await manager.disconnect()
    except Exception as e:
        print(f"Error in test_db_manager teardown: {e}")


@pytest.fixture
async def test_user(test_db_manager) -> User:
    """Create a test user for reviews."""
    
    user = User.create(
        id=uuid4(),
        name="Test User",
        email=f"test_{uuid4()}@example.com",
        profile="https://example.com/profile.jpg"
    )
    
    yield user
    
    try:
        user.delete_instance()
    except Exception:
        pass


@pytest.fixture
async def test_product_id() -> str:
    """Return a mock product ID."""
    return str(uuid4())


def create_test_app(db_manager: DatabaseManager) -> FastAPI:
    """Create and configure FastAPI app instance for testing."""
    settings = config.settings
    
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description="API for product reviews and comments functionality"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(reviews_router, prefix=settings.api_prefix)
    
    @app.get("/", response_model=Dict[str, str])
    async def root():
        return {
            "message": "Welcome to Product Reviews API",
            "version": settings.app_version,
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health_check():
        db_status = db_manager.get_health_status()
        overall_status = "healthy" if db_status["status"] == "healthy" else "unhealthy"
        
        return {
            "status": overall_status,
            "database": db_status,
            "homepage_mongodb": "disconnected",  # Mocked for tests
            "version": settings.app_version
        }
    
    return app


@pytest.fixture
async def client(test_db_manager) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP test client for API testing."""
    # Mock product validator to avoid MongoDB dependency
    original_product_exists = product_validator.product_exists
    
    async def mock_product_exists(product_id: str) -> bool:
        return True
    
    product_validator.product_exists = mock_product_exists
    
    try:
        test_app = create_test_app(test_db_manager)
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        product_validator.product_exists = original_product_exists

