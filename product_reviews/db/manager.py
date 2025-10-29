"""Database connection and utilities."""

import logging
import config
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from peewee import PostgresqlDatabase

from db.models import database, MODELS, check_tables_exist

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.is_connected = False
    
    async def connect(self):
        """Connect to database and create tables if needed."""
        try:
            settings = config.settings
            
            # Close existing connection if open
            if not database.is_closed():
                database.close()
            
            database.init(
                database=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                host=settings.db_host,
                port=settings.db_port
            )
            
            database.connect(reuse_if_open=True)
            
            # Verify connection is actually open
            if database.is_closed():
                raise RuntimeError("Database connection failed to open after connect() call")
            
            # Verify connection with a test query
            database.execute_sql('SELECT 1')
            
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


db_manager = DatabaseManager()
