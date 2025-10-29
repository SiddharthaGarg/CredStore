"""User Data Access Object."""

import logging
from typing import Optional, List
from uuid import UUID

from peewee import DoesNotExist
from db.models import User
from .base_dao import BaseDAO, DAOException

logger = logging.getLogger(__name__)


class UserDAO(BaseDAO):
    """DAO for User operations."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return User.get(User.email == email)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise DAOException(f"Failed to get user by email: {e}")
    
    def create_user(self, name: str, email: str, profile: str = None) -> User:
        """Create a new user."""
        try:
            return self.create(
                name=name,
                email=email,
                profile=profile
            )
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            raise DAOException(f"Failed to create user: {e}")
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists by ID."""
        try:
            return User.select().where(User.id == UUID(user_id)).exists()
        except ValueError:
            return False
        except Exception as e:
            logger.error(f"Error checking user existence {user_id}: {e}")
            return False
    
