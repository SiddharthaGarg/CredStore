"""FastAPI application for Product Reviews module."""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from config import settings
from db.manager import db_manager
from api.routers import reviews_router
from services import product_validator
from events import setup_event_handlers
from events.event_bus import event_bus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Product Reviews API...")
    try:
        await db_manager.connect()
        logger.info("Database connection established")
        
        # Connect to homepage MongoDB for product validation
        await product_validator.connect()
        if product_validator.is_connected():
            logger.info("Homepage MongoDB connection established")
        else:
            logger.warning("Homepage MongoDB connection failed - product validation will be skipped")
        
        # Setup event handlers
        setup_event_handlers()
        logger.info("Event handlers registered")
            
    except Exception as e:
        logger.error(f"Failed to establish database connections: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Product Reviews API...")
    event_bus.shutdown()
    await db_manager.disconnect()
    await product_validator.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="API for product reviews and comments functionality",
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


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "data": None,
            "err": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": error_details
            }
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors."""
    logger.error(f"Internal server error on {request.url}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "err": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred"
            }
        }
    )


# Include routers
app.include_router(reviews_router, prefix=settings.api_prefix)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Product Reviews API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = db_manager.get_health_status()
    
    overall_status = "healthy" if db_status["status"] == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "database": db_status,
        "homepage_mongodb": "connected" if product_validator.is_connected() else "disconnected",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port from homepage module
        reload=settings.debug,
        log_level="info"
    )
