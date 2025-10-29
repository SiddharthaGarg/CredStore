"""Database connection and utilities."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from models import database, MODELS
from config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.is_connected = False
    
    async def connect(self):
        """Connect to database and create tables if needed."""
        try:
            if not database.is_closed():
                database.close()
            
            # Connect to database
            database.connect(reuse_if_open=True)
            
            # Test connection
            database.execute_sql('SELECT 1')
            
            # Check if tables exist (created by Liquibase migrations)
            from models import check_tables_exist
            if not check_tables_exist():
                logger.warning("Database tables not found. Please run Liquibase migrations first.")
                logger.info("Run: docker-compose run --rm liquibase")
            else:
                logger.info("Database tables verified")
            
            self.is_connected = True
            logger.info("Successfully connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from database."""
        try:
            if not database.is_closed():
                database.close()
            
            self.is_connected = False
            logger.info("Disconnected from database")
            
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
    
    def get_health_status(self) -> dict:
        """Get database health status."""
        try:
            if database.is_closed():
                return {"status": "disconnected", "message": "Database connection is closed"}
            
            # Test with a simple query
            database.execute_sql('SELECT 1')
            return {"status": "healthy", "message": "Database connection is active"}
            
        except Exception as e:
            return {"status": "unhealthy", "message": f"Database error: {str(e)}"}


@asynccontextmanager
async def get_db_transaction():
    """Get database transaction context manager."""
    with database.atomic() as transaction:
        try:
            yield transaction
        except Exception:
            transaction.rollback()
            raise


def get_db():
    """Dependency for getting database instance."""
    return database


# Global database manager instance
db_manager = DatabaseManager()
