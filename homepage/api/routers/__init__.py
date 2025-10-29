"""API routers package."""

from .products import ProductRouter
from .admin import AdminProductRouter

__all__ = ["ProductRouter", "AdminProductRouter"]

