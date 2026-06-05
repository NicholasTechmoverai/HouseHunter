from pydantic import BaseModel, Field, validator
from typing import Optional, List,Dict,Any
from decimal import Decimal
from datetime import datetime
import re

# from ...models.for_rent.rental import PropertyCategory, RentalStatus


# class RentalCreate(BaseModel):
#     title: str = Field(..., min_length=5, max_length=200)
#     description: str = Field(..., min_length=50, max_length=5000)
#     category: PropertyCategory
#     bedrooms: int = Field(1, ge=0)
#     bathrooms: Decimal = Field(1.0, ge=0, le=50)
#     area_sqft: Optional[Decimal] = Field(None, ge=0)
#     price: Optional[Decimal] = Field(None, ge=0)

#     country: str = Field(..., max_length=100)
#     city: str = Field(..., max_length=100)
#     state: str = Field(..., max_length=100)
#     address: str = Field(..., min_length=5)
#     zip_code: Optional[str] = Field(None, max_length=20)
#     latitude: Optional[float] = Field(None, ge=-90, le=90)
#     longitude: Optional[float] = Field(None, ge=-180, le=180)

#     year_built: Optional[int] = Field(None, ge=1800, le=datetime.now().year)
#     lot_size: Optional[int] = Field(None, ge=0)
#     floor_number: Optional[int] = Field(None, ge=0)
#     contact_number: Optional[str] = Field(None, max_length=20)

#     profile_picture: Optional[str] = Field(None, max_length=500)
#     theme_color: Optional[str] = Field("#FFFFFF", max_length=7)

#     available_from: Optional[datetime] = None
#     status: RentalStatus = RentalStatus.DRAFT



# Response models
class RentalResponse(BaseModel):
    id: str
    title: str
    description: str
    price: float
    currency: str
    location: str
    amenities: List[str]
    images: List[str]
    created_at: datetime
    updated_at: datetime
    # Add other rental fields as needed


class ListRentalResponse(BaseModel):
    success: bool
    message: str
    data: List[Dict[str, Any]]
    pagination: Optional[Dict[str, Any]] = None




