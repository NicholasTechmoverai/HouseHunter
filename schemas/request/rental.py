from fastapi import Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any



class Location(BaseModel):
    lat: Decimal
    long: Decimal

class SearchRequest(BaseModel):
    query: str
    near_me: Optional[Location] = None
    radius: Optional[float] = Field(None, description="Search radius in km")
    
    category: Optional[List[str]] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    amenities: Optional[List[str]] = None
    status: Optional[List[str]] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None

    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field("asc", description="Sort order: 'asc' or 'desc'")
    page: Optional[int] = Field(1, ge=1)
    page_size: Optional[int] = Field(20, ge=1, le=100)

    user_id: Optional[str] = None
    favorites_only: Optional[bool] = False
    user_preferences: Optional[Dict[str, str]] = None
    
    
class PropertyRuleCreate(BaseModel):
    title: str
    description: str
    is_mandatory: bool = True

class AmenityCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = ""
    icon: Optional[str] = "i-heroicons-truck"
    is_free: bool = True
    sort_order: int = 1

class HeadInfoCreate(BaseModel):
    """Schema for creating new head information."""
    title: str
    description: str
    category: int|str
    theme_color: str = "#FFFFFF"
    profile_picture: Optional[str] = None


class HeadInfoResponse(BaseModel):
    """Response model for head information"""
    data: dict
    success: bool = Field(default=True)
    message: str = Field(default="Operation successful")

class HeadInfoRecord(BaseModel):
    """Schema for stored head information with metadata."""
    data: HeadInfoCreate
    lastUpdated: datetime
    status: str
    
class LocationCreate(BaseModel):
    address: str
    city: str
    coordinates: Optional[dict] = None
    country: str
    state: str



from decimal import Decimal
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ExtraFee(BaseModel):
    id: str
    name:str
    code:str
    is_included:Optional[bool] = False
    description: Optional[str] = None
    amount: Decimal | str | None = None


class PriceCreate(BaseModel):
    amount: Decimal
    period: Literal['daily', 'weekly', 'monthly', 'quarterly', 'annually']
    currency: str

    deposit_amount: Optional[Decimal] = Field(None, alias='depositAmount')
    deposit_type: Optional[Literal[
        'One month rent',
        'Two months rent',
        'Fixed amount',
        'Negotiable'
    ]] = Field(None, alias='depositType')

    is_refundable: bool = Field(..., alias='isRefundable')
    min_rent_period: int = Field(..., alias='minRentPeriod')

    utilities_included: bool = Field(False, alias='utilitiesIncluded')

    discount:Optional[Decimal] = None

    extra_fees: List[ExtraFee] = Field(default_factory=list, alias='extraFees')

    class Config:
        populate_by_name = True


class FileUploadResponse(BaseModel):
    url: str
    filename: str
    content_type: str
    size: int


class RentalCreate(BaseModel):
    head_info: HeadInfoCreate
    location: LocationCreate
    price: PriceCreate
    amenities: List[AmenityCreate] = Field(default_factory=list)
    property_rules: List[PropertyRuleCreate] = Field(default_factory=list)
    rules_content: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Files are metadata only (URLs, filenames) - NOT binary data
    files: List[Dict[str, Any]] = Field(default_factory=list)
    
    @field_validator("files", mode="before")
    @classmethod
    def sanitize_files(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("files must be a list")
        for item in value:
            if isinstance(item, (bytes, bytearray)):
                raise ValueError(
                    "Binary data is not allowed in 'files'. "
                    "Use base64 strings or upload files via multipart/form-data."
                )
        return value
    
    
    
    
class RentalFilter(BaseModel):
    lat: Optional[Decimal] = None,
    long: Optional[Decimal] = None,
    radius: Optional[float] = 10,
    category: Optional[List[str]] = Query(None),
    price_min: Optional[Decimal] = None,
    price_max: Optional[Decimal] = None,
    amenities: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: Optional[str] = Query(None, description="Sort by: price_asc, price_desc, newest, featured"),
    is_featured: Optional[bool] = None,
    is_verified: Optional[bool] = True