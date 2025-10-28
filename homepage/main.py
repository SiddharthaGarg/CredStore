"""FastAPI application for App Store Homepage module."""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from math import ceil

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import mongodb, elasticsearch_client
from models import (
    ProductCreate, ProductResponse, ProductListResponse, 
    SearchResponse, ProductInDB, ProductUpdate
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up the application...")
    try:
        await mongodb.connect()
        await elasticsearch_client.connect()
        logger.info("All database connections established")
    except Exception as e:
        logger.error(f"Failed to establish database connections: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down the application...")
    await mongodb.disconnect()
    await elasticsearch_client.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="API for App Store-like homepage functionality",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_product_to_response(product: ProductInDB) -> ProductResponse:
    """Convert ProductInDB to ProductResponse."""
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


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to App Store Homepage API",
        "version": settings.app_version
    }


@app.post("/admin/products", response_model=ProductResponse, status_code=201)
async def add_product(product_data: ProductCreate):
    """Add a new product (Admin API)."""
    try:
        # Create product in MongoDB
        product = await mongodb.create_product(product_data)
        
        # Index product in Elasticsearch for search
        await elasticsearch_client.index_product(product)
        
        logger.info(f"Product {product.name} created successfully with ID: {product.id}")
        return convert_product_to_response(product)
        
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(status_code=500, detail="Failed to create product")


@app.get("/products", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """List products with pagination."""
    try:
        skip = (page - 1) * page_size
        products, total = await mongodb.list_products(skip=skip, limit=page_size, category=category)
        
        product_responses = [convert_product_to_response(product) for product in products]
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
        raise HTTPException(status_code=500, detail="Failed to retrieve products")


@app.get("/products/search", response_model=SearchResponse)
async def search_products(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Search products using Elasticsearch."""
    try:
        skip = (page - 1) * page_size
        search_results, total, took = await elasticsearch_client.search_products(
            query=q, skip=skip, limit=page_size, category=category
        )
        
        # Convert search results to product responses
        product_responses = []
        for result in search_results:
            # Get full product data from MongoDB for consistency
            product = await mongodb.get_product(result["id"])
            if product:
                product_responses.append(convert_product_to_response(product))
        
        return SearchResponse(
            products=product_responses,
            total=total,
            query=q,
            took=took
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a specific product by ID."""
    try:
        product = await mongodb.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        return convert_product_to_response(product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve product")


@app.put("/admin/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, update_data: ProductUpdate):
    """Update a product (Admin API)."""
    try:
        product = await mongodb.update_product(product_id, update_data)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        # Update in Elasticsearch
        await elasticsearch_client.index_product(product)
        
        logger.info(f"Product {product_id} updated successfully")
        return convert_product_to_response(product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update product")


@app.delete("/admin/products/{product_id}")
async def delete_product(product_id: str):
    """Delete a product (Admin API)."""
    try:
        # Check if product exists
        existing_product = await mongodb.get_product(product_id)
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete from MongoDB
        success = await mongodb.delete_product(product_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete product")
            
        # Delete from Elasticsearch
        await elasticsearch_client.delete_product(product_id)
        
        logger.info(f"Product {product_id} deleted successfully")
        return {"message": "Product deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete product")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mongodb": "connected" if mongodb.client else "disconnected",
        "elasticsearch": "connected" if elasticsearch_client.client else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
