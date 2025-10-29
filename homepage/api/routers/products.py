"""Products API router."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path, status

from api.schemas import ProductResponse, ProductListResponse, SearchResponse
from services.product_service import ProductService, ServiceException, NotFoundException

logger = logging.getLogger(__name__)


class ProductRouter:
    """Class-based router for product endpoints."""
    
    def __init__(self, product_service: ProductService):
        self.product_service = product_service
        
        self.router = APIRouter(prefix="/products", tags=["products"])
        self._register_routes()
    
    def _register_routes(self):
        self.router.add_api_route(
            "",
            self.list_products,
            methods=["GET"],
            response_model=ProductListResponse
        )
        self.router.add_api_route(
            "/search",
            self.search_products,
            methods=["GET"],
            response_model=SearchResponse
        )
        self.router.add_api_route(
            "/{product_id}",
            self.get_product,
            methods=["GET"],
            response_model=ProductResponse
        )
    
    async def _handle_service_exceptions(self, func, *args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotFoundException as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": e.code, "message": e.message}
            )
        except ServiceException as e:
            logger.error(f"Service error: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": e.code, "message": e.message}
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
            )
    
    async def list_products(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        category: Optional[str] = Query(None, description="Filter by category")
    ):
        return await self._handle_service_exceptions(
            self.product_service.list_products, page, page_size, category
        )
    
    async def search_products(
        self,
        q: str = Query(..., description="Search query"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        category: Optional[str] = Query(None, description="Filter by category")
    ):
        return await self._handle_service_exceptions(
            self.product_service.search_products, q, page, page_size, category
        )
    
    async def get_product(
        self,
        product_id: str = Path(..., description="Product ID")
    ):
        return await self._handle_service_exceptions(
            self.product_service.get_product, product_id
        )
