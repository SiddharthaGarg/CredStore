"""Base service class with common functionality."""

import logging
from typing import Optional
from uuid import UUID

from schemas import UserDetails
from dao import UserDAO

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common functionality."""
    
    def __init__(self, user_dao: UserDAO = None):
        self.user_dao = user_dao or UserDAO()
    
    async def get_user_details(self, user_id: str) -> Optional[UserDetails]:
        """Get user details for nested responses."""
        try:
            user = self.user_dao.get_by_id(user_id)
            if user:
                return UserDetails(
                    id=str(user.id),
                    name=user.name,
                    profile=user.profile
                )
            return None
        except Exception:
            return None
    
    async def validate_user_exists(self, user_id: str) -> bool:
        """Validate that a user exists."""
        return self.user_dao.user_exists(user_id)
    
    def _log_operation(self, operation: str, item_id: str, success: bool, error: str = None):
        """Log service operations."""
        if success:
            logger.info(f"{operation} successful for item {item_id}")
        else:
            logger.error(f"{operation} failed for item {item_id}: {error}")


class ServiceException(Exception):
    """Base exception for service layer."""
    
    def __init__(self, message: str, code: str = "SERVICE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationException(ServiceException):
    """Exception for validation errors."""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundException(ServiceException):
    """Exception for not found errors."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with ID {identifier} not found"
        super().__init__(message, "NOT_FOUND")


class PermissionException(ServiceException):
    """Exception for permission errors."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "PERMISSION_DENIED")

