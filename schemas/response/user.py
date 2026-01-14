from pydantic import BaseModel, EmailStr,HttpUrl
from typing import Optional, Dict, Any, List,Literal
from decimal import Decimal
from datetime import datetime, date



# --------------------------------------------------------------------
# LEVEL 1 PROFILE (minimal public profile)
# --------------------------------------------------------------------
class Lv1_Profile(BaseModel):
    public_id: Optional[str] = None
    username: str = ""
    display_name: Optional[str] = None
    profile_picture: Optional[str] = None
    profile_picture_thumbnail: Optional[str] = None
    email: Optional[EmailStr] = None
    is_email_verified: Optional[bool] = None
    status: Optional[str] = None



class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: Lv1_Profile
    message: Optional[str] = "Login successful"
    success: bool = True


# --------------------------------------------------------------------
# LEVEL 2 PROFILE (medium detail)
# --------------------------------------------------------------------
class Lv2_Profile(BaseModel):
    public_id: str
    username: str
    display_name: Optional[str]
    email: EmailStr
    profile_picture: Optional[str]
    profile_picture_thumbnail: Optional[str]

    # Basic personal info
    tagline: Optional[str]
    bio: Optional[str]
    occupation: Optional[str]

    # basic location
    current_country: Optional[str]
    current_city: Optional[str]


# FULL PROFILE (all details from BaseUser + User)
class FullProfile(BaseModel):
    id: str
    public_id: str

    email: EmailStr
    email_verified: bool
    email_verified_at: Optional[str]

    username: str
    display_name: Optional[str]

    first_name: str
    last_name: str
    middle_name: Optional[str]

    date_of_birth: Optional[str]
    gender: Optional[int]

    phone_number: Optional[str]
    phone_country_code: str
    phone_verified: bool
    phone_verified_at: Optional[str]

    secondary_email: Optional[str]
    secondary_phone: Optional[str]

    oauth_providers: Dict[str, Any]
    
    country: str
    timezone: str
    locale: str
    currency: str

    account_type: int
    status: int

    last_login: Optional[str]
    last_login_ip: Optional[str]
    last_active: Optional[str]

    preferences: Dict[str, Any]

    consent_given: bool
    consent_given_at: Optional[str]
    gdpr_consents: Optional[Dict[str, Any]]
    data_processing_consent: bool

    signup_source: Optional[str]
    signup_ip: Optional[str]
    signup_user_agent: Optional[str]

    referral_code: Optional[str]
    referred_by: Optional[str]  # public_id or id

    profile_picture: Optional[str]
    profile_picture_thumbnail: Optional[str]
    profile_banner: Optional[str]

    verification_level: int
    id_verified: bool
    id_verified_at: Optional[str]
    id_document_type: Optional[str]
    id_document_number: Optional[str]

    account_tier: str
    

    bio: Optional[str]
    tagline: Optional[str]
    website: Optional[str]

    occupation: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    industry: Optional[str]

    current_city: Optional[str]
    current_country: Optional[str]
    current_state: Optional[str]
    current_postal_code: Optional[str]
    current_address: Optional[str]

    home_city: Optional[str]
    home_country: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]

    social_links: Dict[str, Any]

    profile_views: int
    property_views: int
    search_count: int

    wallet_balance: Decimal
    total_spent: Decimal
    total_earned: Decimal

    subscription_tier: Optional[str]
    subscription_start: Optional[str]
    subscription_end: Optional[str]
    subscription_auto_renew: bool

    categories_of_interest: List[Any]


class AccountItem(BaseModel):
    id: str
    name: str
    verified: bool
    status: Literal["active", "pending", "suspended"]
    created_at: str

class Account(BaseModel):
    currentAccount: str
    availableAccounts: List[AccountItem]


class Email(BaseModel):
    email: str
    email_verified: bool

class PhoneNumber(BaseModel):
    country_code: str
    number: str
    phone_verified: bool

class Coordinates(BaseModel):
    lat: float
    long: float

class Location(BaseModel):
    country: str
    county: str
    state: str
    city: str
    address: str
    coordinates: Coordinates


class UserPersonalProfile(BaseModel):
    account: Account
    name: str
    profile_picture: HttpUrl
    userName: str
    publicId: str

    email: Email
    phone_number: PhoneNumber
    location: Location

    currency: str
    locale: str
    bio: str
    occupation: str
    company: str
    job_title: str
    industry: str
    website: HttpUrl

    status: Literal["free", "premium", "enterprise"]
    date_of_birth: date
    gender: Literal["Male", "Female", "Other"]

    created_at: datetime
    last_active: datetime
    verification_level: Literal["basic", "verified", "premium"]
