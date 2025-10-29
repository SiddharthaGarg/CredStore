"""Database connection manager."""

import logging
import config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from elasticsearch import AsyncElasticsearch

from db.dao import ProductDAO, SearchDAO

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager for MongoDB and Elasticsearch."""
    
    def __init__(self):
        self.mongodb_client: AsyncIOMotorClient = None
        self.mongodb_database: AsyncIOMotorDatabase = None
        self.mongodb_collection: AsyncIOMotorCollection = None
        self.elasticsearch_client: AsyncElasticsearch = None
        
        self.product_dao = ProductDAO()
        self.search_dao = SearchDAO()
    
    async def connect(self):
        """Connect to MongoDB and Elasticsearch."""
        try:
            await self._connect_mongodb()
            await self._connect_elasticsearch()
            logger.info("All database connections established")
        except Exception as e:
            logger.error(f"Failed to establish database connections: {e}")
            raise
    
    async def _connect_mongodb(self):
        """Connect to MongoDB."""
        try:
            settings = config.settings
            self.mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
            self.mongodb_database = self.mongodb_client[settings.mongodb_database]
            self.mongodb_collection = self.mongodb_database[settings.mongodb_collection]
            
            await self.mongodb_client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            self.product_dao.set_collection(self.mongodb_database, self.mongodb_collection)
            await self.product_dao.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def _connect_elasticsearch(self):
        """Connect to Elasticsearch."""
        try:
            settings = config.settings
            self.elasticsearch_client = AsyncElasticsearch(
                [settings.elasticsearch_url],
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            info = await self.elasticsearch_client.info()
            logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
            
            self.search_dao.set_client(self.elasticsearch_client, settings.elasticsearch_index)
            await self.search_dao.create_index()
            
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            logger.warning("Starting application without Elasticsearch search functionality")
            self.elasticsearch_client = None
    
    async def disconnect(self):
        """Disconnect from all databases."""
        if self.mongodb_client:
            self.mongodb_client.close()
            logger.info("Disconnected from MongoDB")
        
        if self.elasticsearch_client:
            await self.elasticsearch_client.close()
            logger.info("Disconnected from Elasticsearch")
    
    def get_health_status(self) -> dict:
        """Get database health status."""
        mongodb_status = "connected" if self.mongodb_client else "disconnected"
        elasticsearch_status = "connected" if self.elasticsearch_client else "disconnected"
        
        return {
            "mongodb": mongodb_status,
            "elasticsearch": elasticsearch_status
        }


db_manager = DatabaseManager()

