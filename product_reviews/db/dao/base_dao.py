"""Base Data Access Object with common functionality."""

import logging
from typing import Optional, List, Type, Any, Dict
from uuid import UUID
from abc import ABC, abstractmethod

from peewee import Model, DoesNotExist, IntegrityError

logger = logging.getLogger(__name__)


class BaseDAO(ABC):
    """Base DAO class with common database operations."""
    
    def __init__(self, model: Type[Model]):
        self.model = model
    
    def get_by_id(self, item_id: str) -> Optional[Model]:
        """Get item by ID."""
        try:
            return self.model.get_by_id(UUID(item_id))
        except (DoesNotExist, ValueError):
            return None
    
    def create(self, **kwargs) -> Model:
        """Create a new record."""
        try:
            return self.model.create(**kwargs)
        except IntegrityError as e:
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def update(self, instance: Model, **kwargs) -> Model:
        """Update an existing record."""
        try:
            for key, value in kwargs.items():
                if hasattr(instance, key) and value is not None:
                    setattr(instance, key, value)
            instance.save()
            return instance
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    def delete(self, instance: Model) -> bool:
        """Delete a record."""
        try:
            instance.delete_instance()
            return True
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            return False
    
    def exists(self, **conditions) -> bool:
        """Check if record exists with given conditions."""
        try:
            return self.model.select().where(*self._build_conditions(**conditions)).exists()
        except Exception as e:
            logger.error(f"Error checking existence in {self.model.__name__}: {e}")
            return False
    
    def find_one(self, **conditions) -> Optional[Model]:
        """Find one record by conditions."""
        try:
            return self.model.select().where(*self._build_conditions(**conditions)).first()
        except Exception as e:
            logger.error(f"Error finding record in {self.model.__name__}: {e}")
            return None
    
    def find_many(self, limit: int = None, offset: int = None, order_by=None, **conditions) -> List[Model]:
        """Find multiple records by conditions."""
        try:
            query = self.model.select().where(*self._build_conditions(**conditions))
            
            if order_by:
                query = query.order_by(order_by)
            
            if offset:
                query = query.offset(offset)
                
            if limit:
                query = query.limit(limit)
            
            return list(query)
        except Exception as e:
            logger.error(f"Error finding records in {self.model.__name__}: {e}")
            return []
    
    def count(self, **conditions) -> int:
        """Count records matching conditions."""
        try:
            return self.model.select().where(*self._build_conditions(**conditions)).count()
        except Exception as e:
            logger.error(f"Error counting records in {self.model.__name__}: {e}")
            return 0
    
    def _build_conditions(self, **conditions):
        """Build peewee conditions from kwargs."""
        conditions_list = []
        for key, value in conditions.items():
            if hasattr(self.model, key):
                field = getattr(self.model, key)
                conditions_list.append(field == value)
        return conditions_list
    
    def _log_operation(self, operation: str, item_id: str, success: bool, error: str = None):
        """Log DAO operations."""
        if success:
            logger.info(f"{operation} successful for {self.model.__name__} {item_id}")
        else:
            logger.error(f"{operation} failed for {self.model.__name__} {item_id}: {error}")


class DAOException(Exception):
    """Base exception for DAO layer."""
    
    def __init__(self, message: str, code: str = "DAO_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)
