"""Search Data Access Object for Elasticsearch operations."""

import logging
from typing import Optional, Dict, Any
from elasticsearch import AsyncElasticsearch

from db.models import ProductInDB

logger = logging.getLogger(__name__)


class SearchDAO:
    """DAO for Elasticsearch search operations."""
    
    def __init__(self, client: AsyncElasticsearch = None, index_name: str = None):
        self._client: Optional[AsyncElasticsearch] = client
        self._index_name: Optional[str] = index_name
    
    def set_client(self, client: AsyncElasticsearch, index_name: str):
        """Set Elasticsearch client and index name."""
        if client is None or index_name is None:
            raise ValueError("Client and index_name must be provided")
        self._client = client
        self._index_name = index_name
    
    @property
    def client(self) -> Optional[AsyncElasticsearch]:
        """Get Elasticsearch client."""
        return self._client
    
    @property
    def index_name(self) -> Optional[str]:
        """Get index name."""
        return self._index_name
    
    async def create_index(self):
        """Create Elasticsearch index with proper mapping."""
        if not self._client or not self._index_name:
            logger.warning("Elasticsearch client or index name not set")
            return
            
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
            if not await self._client.indices.exists(index=self._index_name):
                await self._client.indices.create(
                    index=self._index_name,
                    body=index_mapping
                )
                logger.info("Elasticsearch index created successfully")
        except Exception as e:
            logger.error(f"Failed to create Elasticsearch index: {e}")
    
    async def index_product(self, product: ProductInDB):
        """Index a product in Elasticsearch."""
        if not self._client or not self._index_name:
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
            
            await self._client.index(
                index=self._index_name,
                id=str(product.id),
                body=doc
            )
        except Exception as e:
            logger.error(f"Failed to index product {product.id}: {e}")
    
    async def search_products(self, query: str, skip: int = 0, limit: int = 20, 
                            category: Optional[str] = None) -> tuple[list[Dict[str, Any]], int, int]:
        """Search products."""
        if not self._client or not self._index_name:
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
            
            if category:
                search_body["query"]["bool"]["filter"] = [{"term": {"category": category}}]
            
            response = await self._client.search(
                index=self._index_name,
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
        if not self._client or not self._index_name:
            return
            
        try:
            await self._client.delete(
                index=self._index_name,
                id=product_id
            )
        except Exception as e:
            logger.error(f"Failed to delete product {product_id} from Elasticsearch: {e}")

