"""Admin Products API router."""

import logging
from fastapi import APIRouter, HTTPException, Path, status

from api.schemas import ProductCreate, ProductUpdate, ProductResponse
from services.product_service import ProductService, ServiceException, NotFoundException

logger = logging.getLogger(__name__)


class AdminProductRouter:
    """Class-based router for admin product endpoints."""
    
    def __init__(self, product_service: ProductService):
        self.product_service = product_service
        
        self.router = APIRouter(prefix="/admin/products", tags=["admin"])
        self._register_routes()
    
    def _register_routes(self):
        self.router.add_api_route(
            "",
            self.create_product,
            methods=["POST"],
            response_model=ProductResponse,
            status_code=status.HTTP_201_CREATED
        )
        self.router.add_api_route(
            "/{product_id}",
            self.update_product,
            methods=["PUT"],
            response_model=ProductResponse
        )
        self.router.add_api_route(
            "/{product_id}",
            self.delete_product,
            methods=["DELETE"]
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
    
    async def create_product(
        self,
        product_data: ProductCreate
    ):
        return await self._handle_service_exceptions(
            self.product_service.create_product, product_data
        )
    
    async def update_product(
        self,
        product_id: str = Path(..., description="Product ID"),
        update_data: ProductUpdate = ...
    ):
        return await self._handle_service_exceptions(
            self.product_service.update_product, product_id, update_data
        )
    
    async def delete_product(
        self,
        product_id: str = Path(..., description="Product ID")
    ):
        success = await self._handle_service_exceptions(
            self.product_service.delete_product, product_id
        )
        if success:
            return {"message": "Product deleted successfully"}

