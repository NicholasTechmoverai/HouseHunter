from pydantic import BaseModel, field_validator, EmailStr, Field, validator, HttpUrl

import re
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import date


EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$"

class Login(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    def validate_and_clean_email(cls, v):
        v = v.strip().lower()
        
        if not re.match(EMAIL_REGEX, v):
            raise ValueError("Invalid email format")

        return v
    
    @field_validator("password")
    def validate_password(cls, v):
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v.strip()

    @property
    def cleaned(self):
        return {
            "email": self.email,
            "password": self.password,
        }


class UserIn(BaseModel):
    name: str
    email: EmailStr

    @property
    def cleaned(self):
        return {
            "name": self.name.strip().title(),
            "email": self.email.strip().lower()
        }


    
MAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


class UserCreate(BaseModel):
    """Request model for user registration."""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (minimum 8 characters)",
        examples=["SecurePass123!"]
    )
    
    confirm_password: str = Field(
        ...,
        description="Password confirmation",
        examples=["SecurePass123!"]
    )


    first_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's first name",
        examples=["John"]
    )
    last_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's last name",
        examples=["Doe"]
    )
    
    display_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="User's full name",
        examples=["John Doe"]
    )   
    referral_code: Optional[str] = Field(
        None,
        description="Referral code if any",
        examples=["REF12345"]
    )
    utm_source: Optional[str] = Field(
        None,
        description="UTM source for marketing tracking",
        examples=["google"]
    )
    utm_medium: Optional[str] = Field(
        None,
        description="UTM medium for marketing tracking",
        examples=["cpc"]
    )
    
    current_country: Optional[str] = Field(
        None,
        description="User's current country",
        examples=["USA"]
    )
    current_city: Optional[str] = Field(
        None,
        description="User's current city",
        examples=["New York"]
    )
    home_country: Optional[str] = Field(
        None,
        description="User's home country",
        examples=["USA"]
    )
    home_city: Optional[str] = Field(
        None,
        description="User's home city",
        examples=["New York"]
    )
    current_state: Optional[str] = Field(
        None,
        description="User's current state",
        examples=["NY"]
    )
    current_postal_code: Optional[str] = Field(
        None,
        description="User's current postal code",
        examples=["10001"]
    )
    
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Geographical latitude",
        examples=[40.7128]
    )
    longitude: Optional[float] = Field(
        None,   
        ge=-180,
        le=180,
        description="Geographical longitude",
        examples=[-74.0060]
    ),
    
    ip_address: Optional[str] = Field(
        None,
        description="User's IP address",
        examples=["192.168.1.1"]
    ),
    
    signup_user_agent: Optional[str] = Field(
        None,
        description="User agent string from signup request",
        examples=["Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."]
    )
    

    @field_validator("email")
    @classmethod
    def validate_and_clean_email(cls, v: str) -> str:
        """Validate email format and normalize it."""
        if not v:
            raise ValueError("Email cannot be empty")
        
        v = v.strip().lower()
        
        if not re.match(EMAIL_REGEX, v):
            raise ValueError("Invalid email format")
        
        return v
    

    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password requirements."""
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        
        v = v.strip()
        
        # Add password strength validation if needed
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Optional: Add more complex password rules
        # if not any(char.isdigit() for char in v):
        #     raise ValueError("Password must contain at least one digit")
        # if not any(char.isalpha() for char in v):
        #     raise ValueError("Password must contain at least one letter")
        
        return v
    
    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        """Validate that password and confirm_password match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v
    
    @property
    def cleaned_data(self) -> Dict[str, Any]:
        """Return cleaned data for database insertion."""
        return {
            "email": self.email,
            "password": self.password,  # Should be hashed before storage
            "display_name": self.full_name.strip(),
            "first_name": self.first_name.strip().title(),
            "last_name": self.last_name.strip().title(),
            "referral_code": self.referral_code.strip() if self.referral_code else None,
            "utm_source": self.utm_source.strip() if self.utm_source else None,
            "utm_medium": self.utm_medium.strip() if self.utm_medium else None,
            "current_country": self.current_country.strip() if self.current_country else None,
            "current_city": self.current_city.strip() if self.current_city else None,
            "home_country": self.home_country.strip() if self.home_country else None,
            "home_city": self.home_city.strip() if self.home_city else None,
            "current_state": self.current_state.strip() if self.current_state else None,
            "current_postal_code": self.current_postal_code.strip() if self.current_postal_code else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "signup_ip": self.ip_address.strip() if self.ip_address else None,
            "signup_user_agent": self.signup_user_agent.strip() if self.signup_user_agent else None,   
        }
    
class FileUpload(BaseModel):
    filename: str
    content_type: str





class EditProfile(BaseModel):
    id: str
    public_id: str
    
    email: EmailStr
    email_verified: bool
    username: str
    display_name: Optional[str] = None
    
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[int] = Field(None, ge=0, le=3)
    
    phone_number: Optional[str] = None
    phone_country_code: str
    secondary_email: Optional[EmailStr] = None
    secondary_phone: Optional[str] = None
    
    country: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    currency: Optional[str] = None
    
    profile_pic: Optional[HttpUrl] = None
    profile_pic_thumbnail: Optional[HttpUrl] = None
    profile_banner: Optional[HttpUrl] = None
    bio: Optional[str] = Field(None, max_length=500)
    tagline: Optional[str] = Field(None, max_length=120)
    website: Optional[HttpUrl] = None
    
    occupation: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    
    current_address: Optional[str] = None
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    current_country: Optional[str] = None
    current_postal_code: Optional[str] = None
    
    home_city: Optional[str] = None
    home_country: Optional[str] = None
    
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    id_document_type: Optional[str] = None
    id_document_number: Optional[str] = None
    
    preferences: Dict[str, Any] = Field(default_factory=dict)
    categories_of_interest: List[str] = Field(default_factory=list)
    social_links: Dict[str, HttpUrl] = Field(default_factory=dict)
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        if v is not None:
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 7 or len(digits) > 15:
                raise ValueError("Phone number must be between 7 and 15 digits")
        return v
    
    @validator("date_of_birth")
    def validate_date_of_birth(cls, v):
        if v is not None and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v
    
    def get_update_fields(self) -> Dict[str, Any]:
        excluded_fields = {"id", "public_id", "email", "email_verified"}
        update_data = self.dict(exclude=excluded_fields, exclude_none=True)
        
        if "date_of_birth" in update_data and isinstance(update_data["date_of_birth"], date):
            update_data["date_of_birth"] = update_data["date_of_birth"].isoformat()
        
        return update_data


class PartialProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[int] = Field(None, ge=0, le=3)
    phone_number: Optional[str] = None
    phone_country_code: Optional[str] = None
    
    class Config:
        extra = "forbid" 
  
  