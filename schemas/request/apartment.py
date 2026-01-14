from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl
from datetime import datetime

from models.apartment import ApartmentStatus, ApartmentType


class ApartmentCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    price: float = Field(..., gt=0)
    type: ApartmentType
    bedrooms: int = Field(..., ge=0, le=10)
    bathrooms: int = Field(..., ge=1, le=10)
    area: float = Field(..., gt=0)
    address: str = Field(..., min_length=10, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    amenities: List[str] = Field(default_factory=list)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    @validator('price')
    def validate_price(cls, v):
        if v < 100:
            raise ValueError('Price must be at least 100')
        if v > 10000:
            raise ValueError('Price cannot exceed 10000')
        return round(v, 2)


class ApartmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    type: Optional[ApartmentType] = None
    bedrooms: Optional[int] = Field(None, ge=0, le=10)
    bathrooms: Optional[int] = Field(None, ge=1, le=10)
    area: Optional[float] = Field(None, gt=0)
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    amenities: Optional[List[str]] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    status: Optional[ApartmentStatus] = None


class ApartmentImage(BaseModel):
    url: HttpUrl
    caption: Optional[str] = Field(None, max_length=200)
    is_primary: bool = False


class ApartmentImageUpload(BaseModel):
    images: List[ApartmentImage] = Field(..., min_items=1, max_items=10)
    
    @validator('images')
    def validate_primary_image(cls, v):
        primary_count = sum(1 for img in v if img.is_primary)
        if primary_count > 1:
            raise ValueError('Only one image can be marked as primary')
        return v


class ApartmentPublish(BaseModel):
    publish: bool = True


class ApartmentFeatureUpdate(BaseModel):
    featured: bool = True
    priority: Optional[int] = Field(None, ge=1, le=10)


class ApartmentSearch(BaseModel):
    query: Optional[str] = None
    city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[int] = None
    type: Optional[ApartmentType] = None
    featured: Optional[bool] = None


class ApartmentFilter(BaseModel):
    status: Optional[ApartmentStatus] = None
    type: Optional[ApartmentType] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    city: Optional[str] = None
    amenities: Optional[List[str]] = None


class BulkApartmentUpdate(BaseModel):
    apartment_ids: List[str] = Field(..., min_items=1)
    update_data: Dict[str, Any]
    
    @validator('update_data')
    def validate_update_data(cls, v):
        disallowed_fields = {'id', 'owner_id', 'created_at', 'created_by'}
        for field in disallowed_fields:
            if field in v:
                raise ValueError(f'Cannot update {field}')
        return v