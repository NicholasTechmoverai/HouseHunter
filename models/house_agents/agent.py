from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator, RegexValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
import uuid
from enum import Enum
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
import re
import secrets
import string
from uuid import uuid4

from models.defaults.index import TimestampMixin, SoftDeleteMixin

class AgencyType(Enum):
    INDIVIDUAL = "individual"
    BROKERAGE = "brokerage"
    REALTY_COMPANY = "realty_company"
    PROPERTY_MANAGEMENT = "property_management"

class VerificationStatus(Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class LicenseStatus(Enum):
    UNLICENSED = "unlicensed"
    LICENSED = "licensed"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class Agent(Model, TimestampMixin, SoftDeleteMixin):
    # Core Identification
    id = fields.UUIDField(pk=True, default=uuid4)
    user = fields.OneToOneField(
        "models.User",
        related_name="agent_profile",
        on_delete=fields.CASCADE,
        index=True
    )
    
    # Agency Information
    agency_name = fields.CharField(max_length=200, null=True)
    agency_type = fields.CharEnumField(AgencyType, default=AgencyType.INDIVIDUAL)
    agency_id = fields.CharField(max_length=100, null=True)  # Business registration number
    tax_id = fields.CharField(max_length=50, null=True)  # VAT/Tax identification
    
    # Agent Identification
    public_id = fields.CharField(
        max_length=50, 
        unique=True,
        validators=[RegexValidator(r'^AGNT-[A-Z0-9]{6,}$', 0)]
    )
    license_number = fields.CharField(max_length=100, null=True)
    license_status = fields.CharEnumField(LicenseStatus, default=LicenseStatus.UNLICENSED)
    license_expiry_date = fields.DateField(null=True)
    
    # Contact Information
    office_phone = fields.CharField(
        max_length=20,
        null=True,
        validators=[RegexValidator(r'^\+?[1-9]\d{1,14}$', 0)]
    )
    mobile_phone = fields.CharField(
        max_length=20,
        null=True,
        validators=[RegexValidator(r'^\+?[1-9]\d{1,14}$', 0)]
    )
    whatsapp_number = fields.CharField(max_length=20, null=True)
    secondary_email = fields.CharField(max_length=255, null=True)
    
    # Location
    country = fields.CharField(max_length=100)
    state = fields.CharField(max_length=100)
    county = fields.CharField(max_length=100, null=True)
    city = fields.CharField(max_length=100)
    address = fields.TextField(null=True)
    postal_code = fields.CharField(max_length=20, null=True)
    latitude = fields.FloatField(null=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = fields.FloatField(null=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    
    # Online Presence
    website = fields.CharField(max_length=255, null=True)
    facebook_url = fields.CharField(max_length=255, null=True)
    instagram_url = fields.CharField(max_length=255, null=True)
    linkedin_url = fields.CharField(max_length=255, null=True)
    twitter_url = fields.CharField(max_length=255, null=True)
    
    # Professional Information
    years_of_experience = fields.IntField(default=0, validators=[MinValueValidator(0)])
    specialization = fields.JSONField(default=list)  # e.g., ["residential", "commercial", "rental"]
    languages = fields.JSONField(default=list)  # e.g., ["en", "es", "fr"]
    bio = fields.TextField(null=True)
    certifications = fields.JSONField(default=list)  # List of certifications
    
    # Agent Settings & Permissions
    permissions = fields.JSONField(default={
        "property": {
            "create": True,
            "edit_own": True,
            "edit_all": False,
            "delete_own": True,
            "delete_all": False,
            "view_all": False
        },
        "lead": {
            "view": True,
            "manage": True
        },
        "contract": {
            "create": True,
            "sign": True
        }
    })
    
    # Status & Verification
    is_active = fields.BooleanField(default=True)
    is_verified = fields.BooleanField(default=False)
    verification_status = fields.CharEnumField(VerificationStatus, default=VerificationStatus.UNVERIFIED)
    verification_date = fields.DatetimeField(null=True)
    verified_by = fields.ForeignKeyField(
        "models.AdminUser",
        related_name="verified_agents",
        null=True,
        on_delete=fields.SET_NULL
    )
    
    # Suspension
    is_suspended = fields.BooleanField(default=False)
    suspension_reason = fields.TextField(null=True)
    suspension_until = fields.DatetimeField(null=True)
    suspended_by = fields.ForeignKeyField(
        "models.AdminUser",
        related_name="suspended_agents",
        null=True,
        on_delete=fields.SET_NULL
    )
    
    # Activity Tracking
    last_login_ip = fields.CharField(max_length=45, null=True)
    last_activity = fields.DatetimeField(null=True)
    activity_log = fields.JSONField(default=list)
    login_count = fields.IntField(default=0)
    
    # Agent Stats
    total_listings = fields.IntField(default=0)
    active_listings = fields.IntField(default=0)
    sold_listings = fields.IntField(default=0)
    rented_listings = fields.IntField(default=0)
    total_commission = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_rating = fields.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = fields.IntField(default=0)
    
    # Financial Information
    commission_rate = fields.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    payment_method = fields.JSONField(null=True)  # {"bank": {...}, "paypal": {...}}
    bank_account_details = fields.JSONField(null=True)  # Encrypted bank details
    
    # Preferences
    notification_preferences = fields.JSONField(default={
        "email": True,
        "sms": False,
        "push": True,
        "lead_alerts": True,
        "viewing_updates": True,
        "offer_updates": True
    })
    working_hours = fields.JSONField(default={
        "monday": {"start": "09:00", "end": "17:00", "available": True},
        "tuesday": {"start": "09:00", "end": "17:00", "available": True},
        "wednesday": {"start": "09:00", "end": "17:00", "available": True},
        "thursday": {"start": "09:00", "end": "17:00", "available": True},
        "friday": {"start": "09:00", "end": "17:00", "available": True},
        "saturday": {"start": "10:00", "end": "14:00", "available": False},
        "sunday": {"start": "10:00", "end": "14:00", "available": False}
    })
    
    # Documentation
    profile_picture = fields.CharField(max_length=500, null=True)  # URL to image
    license_document = fields.CharField(max_length=500, null=True)  # URL to license scan
    id_document = fields.CharField(max_length=500, null=True)  # URL to ID scan
    other_documents = fields.JSONField(default=list)  # List of document URLs
    
    class Meta:
        table = "agents"
        indexes = [
            ("public_id",),
            ("license_number",),
            ("agency_name",),
            ("city", "state"),
            ("is_active", "is_verified"),
            ("verification_status",),
            ("average_rating",),
            ("total_listings",),
        ]
        ordering = ["-created_at"]
    
    async def save(self, *args, **kwargs):
        """Override save to auto-generate identifiers."""
        creating = self.pk is None
        
        if creating and not self.public_id:
            self.public_id = await self.generate_unique_public_id()
        
        # Auto-calculate some stats if not set
        if self.active_listings > self.total_listings:
            self.total_listings = self.active_listings
        
        await super().save(*args, **kwargs)
    
    @classmethod
    async def generate_unique_public_id(cls) -> str:
        """Generate a unique public ID for the agent."""
        prefix = "AGNT"
        while True:
            random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            public_id = f"{prefix}-{random_suffix}"
            
            exists = await cls.filter(public_id=public_id).exists()
            if not exists:
                return public_id
    
    async def verify(self, verified_by_user) -> None:
        """Verify the agent."""
        self.is_verified = True
        self.verification_status = VerificationStatus.VERIFIED
        self.verification_date = datetime.utcnow()
        self.verified_by = verified_by_user
        await self.save(update_fields=["is_verified", "verification_status", "verification_date", "verified_by"])
    
    async def update_stats(self) -> None:
        """Update agent statistics."""
        from .property import Property  # Import here to avoid circular imports
        
        total = await Property.filter(agent=self, is_deleted=False).count()
        active = await Property.filter(agent=self, is_active=True, is_deleted=False).count()
        
        self.total_listings = total
        self.active_listings = active
        await self.save(update_fields=["total_listings", "active_listings"])
    
    async def add_review(self, rating: float, comment: str = None) -> None:
        """Add a review and update average rating."""
        from .review import Review  # Import here to avoid circular imports
        
        review = Review(
            agent=self,
            rating=rating,
            comment=comment,
            reviewer=self.user  # Assuming reviewer is a User instance
        )
        await review.save()
        
        # Update average rating
        all_reviews = await Review.filter(agent=self).all()
        if all_reviews:
            total_rating = sum([r.rating for r in all_reviews])
            self.average_rating = total_rating / len(all_reviews)
            self.review_count = len(all_reviews)
            await self.save(update_fields=["average_rating", "review_count"])
    
    async def has_permission(self, module: str, action: str) -> bool:
        """Check if agent has specific permission."""
        module_perms = self.permissions.get(module, {})
        return module_perms.get(action, False)
    
    async def log_activity(self, action: str, details: Dict[str, Any], ip_address: str = None) -> None:
        """Log agent activity."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "ip_address": ip_address or self.last_login_ip
        }
        
        # Keep only last 100 activities
        self.activity_log = [log_entry] + self.activity_log[:99]
        self.last_activity = datetime.utcnow()
        await self.save(update_fields=["activity_log", "last_activity"])
    
    async def suspend(self, reason: str, suspended_by_user, until: Optional[datetime] = None) -> None:
        """Suspend the agent."""
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspension_until = until
        self.suspended_by = suspended_by_user
        await self.save(update_fields=["is_suspended", "suspension_reason", "suspension_until", "suspended_by"])
    
    async def unsuspend(self) -> None:
        """Unsuspend the agent."""
        self.is_suspended = False
        self.suspension_reason = None
        self.suspension_until = None
        self.suspended_by = None
        await self.save(update_fields=["is_suspended", "suspension_reason", "suspension_until", "suspended_by"])
    
    async def is_license_valid(self) -> bool:
        """Check if agent's license is valid."""
        if not self.license_number or self.license_status != LicenseStatus.LICENSED:
            return False
        
        if self.license_expiry_date and self.license_expiry_date < date.today():
            self.license_status = LicenseStatus.EXPIRED
            await self.save(update_fields=["license_status"])
            return False
        
        return True
    
    async def get_contact_info(self) -> Dict[str, Any]:
        """Get formatted contact information."""
        return {
            "name": self.user.get_full_name() if self.user else self.agency_name,
            "agency": self.agency_name,
            "office_phone": self.office_phone,
            "mobile_phone": self.mobile_phone,
            "whatsapp": self.whatsapp_number,
            "email": self.secondary_email or (self.user.email if self.user else None),
            "website": self.website,
            "address": {
                "street": self.address,
                "city": self.city,
                "county": self.county,
                "state": self.state,
                "country": self.country,
                "postal_code": self.postal_code
            },
            "social_media": {
                "facebook": self.facebook_url,
                "instagram": self.instagram_url,
                "linkedin": self.linkedin_url,
                "twitter": self.twitter_url
            }
        }
    
    @property
    def is_available_now(self) -> bool:
        """Check if agent is available based on working hours."""
        if not self.is_active or self.is_suspended:
            return False
        
        now = datetime.utcnow()
        day_name = now.strftime("%A").lower()
        
        if day_name not in self.working_hours:
            return False
        
        day_schedule = self.working_hours[day_name]
        if not day_schedule.get("available", False):
            return False
        
        # Check if within working hours
        try:
            start_time = datetime.strptime(day_schedule["start"], "%H:%M").time()
            end_time = datetime.strptime(day_schedule["end"], "%H:%M").time()
            current_time = now.time()
            
            return start_time <= current_time <= end_time
        except:
            return True  # If time parsing fails, assume available
    
    @property
    def display_name(self) -> str:
        """Get display name for the agent."""
        if self.agency_name and self.user:
            return f"{self.user.get_full_name()} - {self.agency_name}"
        elif self.user:
            return self.user.get_full_name()
        else:
            return self.agency_name or "Unknown Agent"
    
    def __str__(self):
        return f"{self.display_name} ({self.public_id})"