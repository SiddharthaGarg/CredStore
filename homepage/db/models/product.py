"""Product database model."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
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


class ProductInDB(BaseModel):
    """Product model as stored in database."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: str
    developer: str
    category: str
    price: float
    version: str
    rating: float | None = None
    download_count: int = 0
    icon_url: str | None = None
    screenshots: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

