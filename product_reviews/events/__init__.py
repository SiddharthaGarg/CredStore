"""Event system for product reviews module."""

from .event_bus import EventBus, event_bus
from .review_events import ReviewCreated, ReviewUpdated, ReviewDeleted
from .handlers import setup_event_handlers

__all__ = [
    'EventBus',
    'event_bus',
    'ReviewCreated',
    'ReviewUpdated',
    'ReviewDeleted',
    'setup_event_handlers',
]

