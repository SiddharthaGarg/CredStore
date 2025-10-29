"""Product service for business logic."""

import logging
from typing import List, Optional
from math import ceil

from api.schemas import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, SearchResponse
from db.dao import ProductDAO, SearchDAO
from db.models import ProductInDB

logger = logging.getLogger(__name__)


class ServiceException(Exception):
    """Base exception for service layer."""
    
    def __init__(self, message: str, code: str = "SERVICE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundException(ServiceException):
    """Exception for not found errors."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with ID {identifier} not found"
        super().__init__(message, "NOT_FOUND")


class ProductService:
    """Service for product operations."""
    
    def __init__(self, product_dao: ProductDAO = None, search_dao: SearchDAO = None):
        if product_dao is None or search_dao is None:
            raise ValueError("ProductDAO and SearchDAO must be provided")
        self.product_dao = product_dao
        self.search_dao = search_dao
    
    def _convert_to_response(self, product: ProductInDB) -> ProductResponse:
        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            developer=product.developer,
            category=product.category,
            price=product.price,
            version=product.version,
            rating=product.rating,
            download_count=product.download_count,
            icon_url=product.icon_url,
            screenshots=product.screenshots,
            tags=product.tags,
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    
    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        try:
            product = await self.product_dao.create_product(product_data)
            await self.search_dao.index_product(product)
            
            logger.info(f"Product {product.name} created successfully with ID: {product.id}")
            return self._convert_to_response(product)
            
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            raise ServiceException(f"Failed to create product: {str(e)}")
    
    async def get_product(self, product_id: str) -> ProductResponse:
        try:
            product = await self.product_dao.get_product(product_id)
            if not product:
                raise NotFoundException("Product", product_id)
            
            return self._convert_to_response(product)
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            raise ServiceException(f"Failed to retrieve product: {str(e)}")
    
    async def list_products(self, page: int = 1, page_size: int = 20, 
                          category: Optional[str] = None) -> ProductListResponse:
        try:
            skip = (page - 1) * page_size
            products, total = await self.product_dao.list_products(skip=skip, limit=page_size, category=category)
            
            product_responses = [self._convert_to_response(product) for product in products]
            total_pages = ceil(total / page_size) if total > 0 else 0
            
            return ProductListResponse(
                products=product_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list products: {e}")
            raise ServiceException(f"Failed to retrieve products: {str(e)}")
    
    async def update_product(self, product_id: str, update_data: ProductUpdate) -> ProductResponse:
        try:
            product = await self.product_dao.update_product(product_id, update_data)
            if not product:
                raise NotFoundException("Product", product_id)
            
            await self.search_dao.index_product(product)
            
            logger.info(f"Product {product_id} updated successfully")
            return self._convert_to_response(product)
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to update product {product_id}: {e}")
            raise ServiceException(f"Failed to update product: {str(e)}")
    
    async def delete_product(self, product_id: str) -> bool:
        try:
            existing_product = await self.product_dao.get_product(product_id)
            if not existing_product:
                raise NotFoundException("Product", product_id)
            
            success = await self.product_dao.delete_product(product_id)
            if not success:
                raise ServiceException("Failed to delete product")
            
            await self.search_dao.delete_product(product_id)
            
            logger.info(f"Product {product_id} deleted successfully")
            return True
            
        except (NotFoundException, ServiceException):
            raise
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            raise ServiceException(f"Failed to delete product: {str(e)}")
    
    async def search_products(self, query: str, page: int = 1, page_size: int = 20, 
                             category: Optional[str] = None) -> SearchResponse:
        try:
            skip = (page - 1) * page_size
            search_results, total, took = await self.search_dao.search_products(
                query=query, skip=skip, limit=page_size, category=category
            )
            
            product_responses = []
            for result in search_results:
                product = await self.product_dao.get_product(result["id"])
                if product:
                    product_responses.append(self._convert_to_response(product))
            
            return SearchResponse(
                products=product_responses,
                total=total,
                query=query,
                took=took
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise ServiceException(f"Search failed: {str(e)}")

