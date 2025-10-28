"""Database connections and utilities."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from elasticsearch import AsyncElasticsearch
from bson import ObjectId

from config import settings
from models import ProductInDB, ProductCreate, ProductUpdate, ProductResponse

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection and operations."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection: Optional[AsyncIOMotorCollection] = None

    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_database]
            self.collection = self.database[settings.mongodb_collection]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_indexes(self):
        """Create database indexes for better performance."""
        try:
            # Create text index for search
            await self.collection.create_index([
                ("name", "text"),
                ("description", "text"),
                ("developer", "text"),
                ("category", "text"),
                ("tags", "text")
            ])
            
            # Create other indexes
            await self.collection.create_index("category")
            await self.collection.create_index("developer")
            await self.collection.create_index("rating")
            await self.collection.create_index("price")
            await self.collection.create_index("created_at")
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    async def create_product(self, product_data: ProductCreate) -> ProductInDB:
        """Create a new product."""
        product_dict = product_data.model_dump()
        product_dict["created_at"] = datetime.utcnow()
        product_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(product_dict)
        product_dict["_id"] = result.inserted_id
        
        return ProductInDB(**product_dict)

    async def get_product(self, product_id: str) -> Optional[ProductInDB]:
        """Get a product by ID."""
        try:
            product = await self.collection.find_one({"_id": ObjectId(product_id)})
            return ProductInDB(**product) if product else None
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None

    async def list_products(self, skip: int = 0, limit: int = 20, 
                          category: Optional[str] = None) -> tuple[List[ProductInDB], int]:
        """List products with pagination."""
        filter_query = {}
        if category:
            filter_query["category"] = category
            
        # Get total count
        total = await self.collection.count_documents(filter_query)
        
        # Get products
        cursor = self.collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
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
            
            result = await self.collection.update_one(
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
            result = await self.collection.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            return False


class ElasticsearchClient:
    """Elasticsearch client for search functionality."""
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None

    async def connect(self):
        """Connect to Elasticsearch."""
        try:
            # Configure Elasticsearch client for version 8.x with security disabled
            self.client = AsyncElasticsearch(
                [settings.elasticsearch_url],
                verify_certs=False,
                ssl_show_warn=False,
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test the connection with timeout
            info = await self.client.info()
            logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
            
            # Create index if it doesn't exist
            await self.create_index()
            
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            logger.error(f"Elasticsearch URL: {settings.elasticsearch_url}")
            # Don't raise the exception to allow the app to start without Elasticsearch
            logger.warning("Starting application without Elasticsearch search functionality")
            self.client = None

    async def disconnect(self):
        """Disconnect from Elasticsearch."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Elasticsearch")

    async def create_index(self):
        """Create Elasticsearch index with proper mapping."""
        index_mapping = {
            "mappings": {
                "properties": {
                    "name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "description": {"type": "text", "analyzer": "standard"},
                    "developer": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
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
        
        try:
            if not await self.client.indices.exists(index=settings.elasticsearch_index):
                await self.client.indices.create(
                    index=settings.elasticsearch_index,
                    body=index_mapping
                )
                logger.info("Elasticsearch index created successfully")
        except Exception as e:
            logger.error(f"Failed to create Elasticsearch index: {e}")

    async def index_product(self, product: ProductInDB):
        """Index a product in Elasticsearch."""
        # Skip indexing if Elasticsearch is not available
        if not self.client:
            logger.warning("Elasticsearch not available, skipping product indexing")
            return
            
        try:
            doc = {
                "name": product.name,
                "description": product.description,
                "developer": product.developer,
                "category": product.category,
                "price": product.price,
                "version": product.version,
                "rating": product.rating,
                "download_count": product.download_count,
                "tags": product.tags,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat()
            }
            
            await self.client.index(
                index=settings.elasticsearch_index,
                id=str(product.id),
                body=doc
            )
        except Exception as e:
            logger.error(f"Failed to index product {product.id}: {e}")

    async def search_products(self, query: str, skip: int = 0, limit: int = 20, 
                            category: Optional[str] = None) -> tuple[List[Dict[str, Any]], int, int]:
        """Search products."""
        # If Elasticsearch is not available, return empty results
        if not self.client:
            logger.warning("Elasticsearch not available, returning empty search results")
            return [], 0, 0
            
        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["name^2", "description", "developer", "tags"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "from": skip,
                "size": limit,
                "sort": [{"_score": {"order": "desc"}}]
            }
            
            # Add category filter if provided
            if category:
                search_body["query"]["bool"]["filter"] = [{"term": {"category": category}}]
            
            response = await self.client.search(
                index=settings.elasticsearch_index,
                body=search_body
            )
            
            products = []
            for hit in response["hits"]["hits"]:
                product_data = hit["_source"]
                product_data["id"] = hit["_id"]
                products.append(product_data)
            
            total = response["hits"]["total"]["value"]
            took = response["took"]
            
            return products, total, took
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [], 0, 0

    async def delete_product(self, product_id: str):
        """Delete a product from Elasticsearch."""
        if not self.client:
            return
            
        try:
            await self.client.delete(
                index=settings.elasticsearch_index,
                id=product_id
            )
        except Exception as e:
            logger.error(f"Failed to delete product {product_id} from Elasticsearch: {e}")


# Global database instances
mongodb = MongoDB()
elasticsearch_client = ElasticsearchClient()
