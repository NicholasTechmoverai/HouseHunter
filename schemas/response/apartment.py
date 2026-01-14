from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from models.apartment import ApartmentStatus, ApartmentType


class OwnerInfo(BaseModel):
    id: str
    username: str
    display_name: Optional[str]
    profile_pic: Optional[str]
    verified: bool


class ApartmentImage(BaseModel):
    url: str
    caption: Optional[str]
    is_primary: bool
    uploaded_at: datetime


class ApartmentSummary(BaseModel):
    id: str
    title: str
    description: str
    price: float
    type: ApartmentType
    bedrooms: int
    bathrooms: int
    area: Optional[float]
    city: str
    status: ApartmentStatus
    is_featured: bool
    thumbnail: Optional[str]
    created_at: datetime
    updated_at: datetime


class ApartmentDetail(BaseModel):
    id: str
    title: str
    description: str
    price: float
    type: ApartmentType
    bedrooms: int
    bathrooms: int
    area: Optional[float]
    address: str
    city: str
    amenities: List[str]
    latitude: Optional[float]
    longitude: Optional[float]
    status: ApartmentStatus
    is_featured: bool
    feature_priority: Optional[int]
    images: List[ApartmentImage]
    owner: OwnerInfo
    view_count: int = 0
    favorite_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]


class ApartmentList(BaseModel):
    apartments: List[ApartmentSummary]
    total: int
    page: int
    limit: int
    has_more: bool


class ApartmentStats(BaseModel):
    total_apartments: int
    active_apartments: int
    pending_approval: int
    rented_apartments: int
    featured_apartments: int
    by_type: Dict[str, int]
    by_price_range: Dict[str, int]
    avg_price: float
    recent_listings: List[Dict[str, Any]]


class ApartmentAnalytics(BaseModel):
    apartment_id: str
    views: int
    contacts: int
    favorites: int
    period: str
    trend: str
    daily_views: Optional[Dict[str, int]] = None
    source_traffic: Optional[Dict[str, int]] = None


class PriceRange(BaseModel):
    min: float
    max: float
    count: int


class TypeStats(BaseModel):
    type: str
    count: int
    avg_price: float


class CityStats(BaseModel):
    city: str
    count: int
    avg_price: float