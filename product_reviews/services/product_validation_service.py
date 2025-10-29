"""Product validation service to check product existence in homepage MongoDB."""

import logging
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)


class ProductValidationService:
    """Service to validate product existence in homepage MongoDB."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.collection = None
        
        # Homepage MongoDB configuration
        self.mongodb_url = os.getenv("HOMEPAGE_MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_database = os.getenv("HOMEPAGE_MONGODB_DATABASE", "appstore")
        self.mongodb_collection = os.getenv("HOMEPAGE_MONGODB_COLLECTION", "products")
    
    async def connect(self):
        """Connect to homepage MongoDB."""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.database = self.client[self.mongodb_database]
            self.collection = self.database[self.mongodb_collection]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info("Connected to homepage MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to homepage MongoDB: {e}")
            self.client = None
            self.database = None
            self.collection = None
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client is not None:
            self.client.close()
            logger.info("Disconnected from homepage MongoDB")
    
    async def product_exists(self, product_id: str) -> bool:
        """Check if product exists in homepage database."""
        if self.collection is None:
            logger.warning("Homepage MongoDB not connected. Skipping product validation.")
            return True  # Allow operation to continue if MongoDB is not available
        
        try:
            # Validate ObjectId format
            try:
                object_id = ObjectId(product_id)
            except InvalidId:
                logger.warning(f"Invalid ObjectId format: {product_id}")
                return False
            
            # Check if product exists
            product = await self.collection.find_one({"_id": object_id})
            exists = product is not None
            
            if not exists:
                logger.warning(f"Product {product_id} not found in homepage database")
            
            return exists
            
        except Exception as e:
            logger.error(f"Error checking product existence {product_id}: {e}")
            return False  # Allow operation to continue on error
    
    async def get_product_info(self, product_id: str) -> Optional[dict]:
        """Get basic product information from homepage database."""
        if self.collection is None:
            logger.warning("Homepage MongoDB not connected.")
            return None
        
        try:
            object_id = ObjectId(product_id)
            product = await self.collection.find_one(
                {"_id": object_id},
                {"name": 1, "developer": 1, "category": 1}
            )
            
            if product:
                return {
                    "id": str(product["_id"]),
                    "name": product.get("name"),
                    "developer": product.get("developer"),
                    "category": product.get("category")
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting product info {product_id}: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if connected to homepage MongoDB."""
        return self.client is not None and self.collection is not None


# Global instance
product_validator = ProductValidationService()
