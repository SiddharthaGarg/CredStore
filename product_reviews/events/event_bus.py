"""Simple event bus for asynchronous event handling.

This is a lightweight implementation that can later be replaced with
a message queue (RabbitMQ, Redis, Kafka, etc.) without changing the
event emission code."""

import logging
from typing import Callable, Dict, List, Type, TypeVar
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EventBus:
    """Simple event bus for pub/sub pattern."""
    
    def __init__(self):
        self._subscribers: Dict[Type, List[Callable]] = {}
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="event_handler")
        self._main_loop: asyncio.AbstractEventLoop = None
    
    def subscribe(self, event_type: Type[T], handler: Callable[[T], None]):
        """Subscribe a handler to an event type.
        
        Args:
            event_type: The event class to listen for
            handler: Async or sync function that handles the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler {handler.__name__} to {event_type.__name__}")
    
    def publish(self, event: T):
        """Publish an event to all subscribed handlers.
        
        Args:
            event: The event instance to publish
        """
        # Capture the current event loop if we don't have one yet
        try:
            current_loop = asyncio.get_running_loop()
            if self._main_loop is None or not self._main_loop.is_running():
                self._main_loop = current_loop
        except RuntimeError:
            # No running event loop, will handle in executor
            pass
        
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers registered for {event_type.__name__}")
            return
        
        logger.info(f"Publishing {event_type.__name__} to {len(handlers)} handler(s)")
        
        for handler in handlers:
            try:
                self._executor.submit(self._execute_handler, handler, event)
            except Exception as e:
                logger.error(f"Error submitting handler {handler.__name__} for event {event_type.__name__}: {e}")
    
    def _execute_handler(self, handler: Callable, event: T):
        """Execute handler with proper error handling.
        
        This runs in a thread pool executor. For async handlers that use Motor,
        we schedule them back in the main event loop to avoid loop conflicts.
        """
        try:
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                if self._main_loop is not None and self._main_loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(handler(event), self._main_loop)
                    try:
                        future.result(timeout=30)  # Wait up to 30 seconds
                        logger.debug(f"Handler {handler.__name__} executed successfully for {type(event).__name__}")
                    except Exception as e:
                        logger.error(f"Error in async handler {handler.__name__}: {e}", exc_info=True)
                else:
                    # No main loop available, create new one (fallback for testing)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(handler(event))
                        logger.debug(f"Handler {handler.__name__} executed successfully for {type(event).__name__}")
                    finally:
                        loop.close()
            else:
                handler(event)
                logger.debug(f"Handler {handler.__name__} executed successfully for {type(event).__name__}")
        except Exception as e:
            logger.error(f"Error executing handler {handler.__name__}: {e}", exc_info=True)
    
    def shutdown(self):
        """Shutdown the event bus and executor."""
        logger.info("Shutting down event bus...")
        self._executor.shutdown(wait=True)
        logger.info("Event bus shut down")

event_bus = EventBus()

