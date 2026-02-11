from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: List[T] = []
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class BasicResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class AdminUserListItem(BaseModel):
    # id: str
    profile_picture: str
    public_id: str
    display_name: str
    email: str
    country: Optional[str] = None
    email_verified: bool
    id_verified: bool
    status: int
    account_tier: Optional[str] = None
    created_at: datetime


class PublisherInfo(BaseModel):
    public_id: str
    display_name: str
    profile_picture: Optional[str] = "http://localhost:3000/empty_image_placeholder.png"

class AdminRentalListItem(BaseModel):
    public_id: str
    status: str
    created_at: datetime
    title: str
    slug: str
    theme_color: Optional[str] = None
    category: Optional[int] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = "http://localhost:3000/empty_image_placeholder.png"
    price: Optional[float] = None
    deposit: Optional[float] = None
    location: Optional[str] = None
    contact: Optional[str] = None
    available: bool = True
    rating: float = 0.0
    publisher: Optional[PublisherInfo] = None