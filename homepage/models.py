"""Product models and schemas."""

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic models."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        
        def validate_object_id(value: Any, handler_info=None) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str):
                if ObjectId.is_valid(value):
                    return ObjectId(value)
            raise ValueError("Invalid ObjectId")
        
        return core_schema.with_info_plain_validator_function(
            validate_object_id,
            serialization=core_schema.to_string_ser_schema(),
        )


class ProductBase(BaseModel):
    """Base product schema."""
    
    name: str = Field(..., description="Product name", min_length=1, max_length=100)
    description: str = Field(..., description="Product description", max_length=1000)
    developer: str = Field(..., description="Developer name", min_length=1, max_length=100)
    category: str = Field(..., description="Product category")
    price: float = Field(..., ge=0, description="Product price")
    version: str = Field(..., description="Product version")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    download_count: int = Field(default=0, ge=0, description="Number of downloads")
    icon_url: Optional[str] = Field(None, description="Product icon URL")
    screenshots: List[str] = Field(default_factory=list, description="Screenshot URLs")
    tags: List[str] = Field(default_factory=list, description="Product tags for search")


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    developer: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    version: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    download_count: Optional[int] = Field(None, ge=0)
    icon_url: Optional[str] = None
    screenshots: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ProductInDB(ProductBase):
    """Product model as stored in database."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class ProductResponse(BaseModel):
    """Product response schema."""
    
    id: str = Field(..., description="Product ID")
    name: str
    description: str
    developer: str
    category: str
    price: float
    version: str
    rating: Optional[float] = None
    download_count: int
    icon_url: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """Response schema for product lists."""
    
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchResponse(BaseModel):
    """Response schema for product search."""
    
    products: List[ProductResponse]
    total: int
    query: str
    took: int  # Search time in milliseconds
