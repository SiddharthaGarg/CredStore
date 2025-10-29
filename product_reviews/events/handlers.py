"""Event handlers for review events."""

import logging
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from dao.review_dao import ReviewDAO
from services.product_validation_service import product_validator
from .review_events import ReviewCreated, ReviewUpdated, ReviewDeleted

logger = logging.getLogger(__name__)


async def update_product_rating_on_review_created(event: ReviewCreated):
    """Handler for ReviewCreated event - updates product average rating in MongoDB."""
    await _update_product_rating(event.product_id)


async def update_product_rating_on_review_updated(event: ReviewUpdated):
    """Handler for ReviewUpdated event - updates product average rating in MongoDB."""
    await _update_product_rating(event.product_id)


async def update_product_rating_on_review_deleted(event: ReviewDeleted):
    """Handler for ReviewDeleted event - updates product average rating in MongoDB."""
    await _update_product_rating(event.product_id)


async def _update_product_rating(product_id: str):
    """Calculate and update product average rating in homepage MongoDB.
    
    This function:
    1. Calculates average rating from all active reviews for the product
    2. Updates the product document in homepage MongoDB
    """
    try:
        # Check if MongoDB connection is available
        if product_validator.collection is None:
            logger.warning("Cannot update product rating: Homepage MongoDB not connected")
            return
        
        review_dao = ReviewDAO()
        
        # Get all active reviews for this product
        reviews = review_dao.get_reviews_by_product(product_id, limit=10000, offset=0)
        
        if not reviews:
            logger.info(f"No active reviews found for product {product_id}, setting rating to None")
            await _update_mongodb_rating(product_id, None)
            return
        
        # Calculate average rating
        total_rating = sum(review.rating for review in reviews)
        review_count = len(reviews)
        average_rating = round(total_rating / review_count, 2)
        
        logger.info(
            f"Updating product {product_id} rating: "
            f"{average_rating} (from {review_count} reviews)"
        )
        
        # Update MongoDB
        await _update_mongodb_rating(product_id, average_rating)
        
    except Exception as e:
        logger.error(f"Error updating product rating for {product_id}: {e}", exc_info=True)


async def _update_mongodb_rating(product_id: str, rating: Optional[float]):
    """Update the product rating in homepage MongoDB."""
    try:
        if product_validator.collection is None:
            logger.warning("Cannot update MongoDB: collection not available")
            return
        
        # Validate ObjectId format
        if not ObjectId.is_valid(product_id):
            logger.error(f"Invalid product_id format: {product_id}")
            return
        
        object_id = ObjectId(product_id)
        
        # Update product document
        result = await product_validator.collection.update_one(
            {"_id": object_id},
            {"$set": {"rating": rating, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.matched_count == 0:
            logger.warning(f"Product {product_id} not found in homepage MongoDB")
        elif result.modified_count > 0:
            logger.info(f"Successfully updated rating for product {product_id} to {rating}")
        else:
            logger.debug(f"Product {product_id} rating unchanged (already {rating})")
            
    except Exception as e:
        logger.error(f"Error updating MongoDB rating for product {product_id}: {e}", exc_info=True)


def setup_event_handlers():
    """Register all event handlers with the event bus.
    
    This should be called during application startup.
    """
    from .event_bus import event_bus
    
    # Subscribe handlers to events
    event_bus.subscribe(ReviewCreated, update_product_rating_on_review_created)
    event_bus.subscribe(ReviewUpdated, update_product_rating_on_review_updated)
    event_bus.subscribe(ReviewDeleted, update_product_rating_on_review_deleted)
    
    logger.info("Event handlers registered successfully")

