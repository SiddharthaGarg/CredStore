"""User Data Access Object."""

import logging
from typing import Optional, List
from uuid import UUID

from peewee import DoesNotExist
from models import User
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
    
    def update_user(self, user: User, name: str = None, email: str = None, profile: str = None) -> User:
        """Update user information."""
        try:
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if email is not None:
                update_data['email'] = email
            if profile is not None:
                update_data['profile'] = profile
            
            return self.update(user, **update_data)
        except Exception as e:
            logger.error(f"Error updating user {user.id}: {e}")
            raise DAOException(f"Failed to update user: {e}")
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists by ID."""
        try:
            return User.select().where(User.id == UUID(user_id)).exists()
        except ValueError:
            return False
        except Exception as e:
            logger.error(f"Error checking user existence {user_id}: {e}")
            return False
    
    def get_users_by_ids(self, user_ids: List[str]) -> List[User]:
        """Get multiple users by their IDs."""
        try:
            uuid_ids = [UUID(uid) for uid in user_ids if self._is_valid_uuid(uid)]
            return list(User.select().where(User.id.in_(uuid_ids)))
        except Exception as e:
            logger.error(f"Error getting users by IDs: {e}")
            return []
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            UUID(uuid_string)
            return True
        except ValueError:
            return False
