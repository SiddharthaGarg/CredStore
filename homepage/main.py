"""FastAPI application for App Store Homepage module."""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.manager import db_manager
from services.product_service import ProductService
from api.routers import ProductRouter, AdminProductRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting up the application...")
    try:
        await db_manager.connect()
        logger.info("All database connections established")
        
        product_service = ProductService(
            product_dao=db_manager.product_dao,
            search_dao=db_manager.search_dao
        )
        
        product_router = ProductRouter(product_service=product_service)
        admin_product_router = AdminProductRouter(product_service=product_service)
        
        app.include_router(product_router.router)
        app.include_router(admin_product_router.router)
        
    except Exception as e:
        logger.error(f"Failed to establish database connections: {e}")
        raise
    
    yield
    
    logger.info("Shutting down the application...")
    await db_manager.disconnect()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="API for App Store-like homepage functionality",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to App Store Homepage API",
        "version": settings.app_version
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = db_manager.get_health_status()
    overall_status = "healthy" if health_status["mongodb"] == "connected" else "degraded"
    
    return {
        "status": overall_status,
        "mongodb": health_status["mongodb"],
        "elasticsearch": health_status["elasticsearch"],
        "version": settings.app_version
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
