"""Data Access Object (DAO) package for database interactions."""

from .product_dao import ProductDAO
from .search_dao import SearchDAO

__all__ = ["ProductDAO", "SearchDAO"]

