"""Product Data Access Object for MongoDB operations."""

import logging
from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId

from db.models import ProductInDB
from api.schemas import ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)


class ProductDAO:
    """DAO for Product MongoDB operations."""
    
    def __init__(self):
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    def set_collection(self, database: AsyncIOMotorDatabase, collection: AsyncIOMotorCollection):
        """Set database and collection instances."""
        if database is None or collection is None:
            raise ValueError("Database and collection must be provided")
        self._database = database
        self._collection = collection
    
    async def create_indexes(self):
        """Create database indexes for better performance."""
        try:
            await self._collection.create_index([
                ("name", "text"),
                ("description", "text"),
                ("developer", "text"),
                ("category", "text"),
                ("tags", "text")
            ])
            
            await self._collection.create_index("category")
            await self._collection.create_index("developer")
            await self._collection.create_index("rating")
            await self._collection.create_index("price")
            await self._collection.create_index("created_at")
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def create_product(self, product_data: ProductCreate) -> ProductInDB:
        """Create a new product."""
        product_dict = product_data.model_dump()
        product_dict["created_at"] = datetime.utcnow()
        product_dict["updated_at"] = datetime.utcnow()
        
        result = await self._collection.insert_one(product_dict)
        product_dict["_id"] = result.inserted_id
        
        return ProductInDB(**product_dict)
    
    async def get_product(self, product_id: str) -> Optional[ProductInDB]:
        """Get a product by ID."""
        try:
            product = await self._collection.find_one({"_id": ObjectId(product_id)})
            return ProductInDB(**product) if product else None
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None
    
    async def list_products(self, skip: int = 0, limit: int = 20, 
                          category: Optional[str] = None) -> tuple[list[ProductInDB], int]:
        """List products with pagination."""
        filter_query = {}
        if category:
            filter_query["category"] = category
            
        total = await self._collection.count_documents(filter_query)
        
        cursor = self._collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        products = []
        async for product in cursor:
            products.append(ProductInDB(**product))
            
        return products, total
    
    async def update_product(self, product_id: str, update_data: ProductUpdate) -> Optional[ProductInDB]:
        """Update a product."""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            if not update_dict:
                return await self.get_product(product_id)
                
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await self._collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count == 0:
                return None
                
            return await self.get_product(product_id)
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            return None
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product."""
        try:
            result = await self._collection.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            return False

