from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import IntEnum
import random
import string


class SwapType(IntEnum):
    SIMULTANEOUS = 1
    NON_SIMULTANEOUS = 2
    HOSPITALITY = 3
    RENTAL = 4
    LONG_TERM = 5
    SHORT_TERM = 6


class SwapStatus(IntEnum):
    DRAFT = 1
    ACTIVE = 2
    PENDING = 3
    RESERVED = 4
    CONFIRMED = 5
    IN_PROGRESS = 6
    COMPLETED = 7
    CANCELLED = 8
    EXPIRED = 9
    ARCHIVED = 10


class AvailabilityType(IntEnum):
    FLEXIBLE = 1
    SPECIFIC_DATES = 2
    SEASONAL = 3
    WEEKENDS_ONLY = 4
    WEEKDAYS_ONLY = 5


class HouseSwapListing(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    listing_code = fields.CharField(max_length=50, unique=True, index=True)
    title = fields.CharField(max_length=200)
    
    owner = fields.ForeignKeyField(
        'models.User',
        related_name='swap_listings',
        on_delete=fields.CASCADE,
        index=True
    )
    
    apartment = fields.ForeignKeyField(
        'models.ApartmentComplex',
        related_name='swap_listings',
        on_delete=fields.CASCADE,
        null=True,
        index=True
    )
    rental = fields.ForeignKeyField(
        'models.RentalComplex',
        related_name='swap_listings',
        on_delete=fields.CASCADE,
        null=True,
        index=True
    )
    
    desired_locations = fields.JSONField(default=list)
    desired_property_types = fields.JSONField(default=list)
    desired_amenities = fields.JSONField(default=list)
    
    swap_type = fields.IntEnumField(SwapType, default=SwapType.SIMULTANEOUS, index=True)
    min_swap_duration = fields.IntField(default=1)
    max_swap_duration = fields.IntField(null=True)
    preferred_duration = fields.IntField(default=7)
    
    availability_type = fields.IntEnumField(AvailabilityType, default=AvailabilityType.FLEXIBLE)
    available_from = fields.DateField(null=True, index=True)
    available_to = fields.DateField(null=True, index=True)
    blackout_dates = fields.JSONField(default=list)
    advance_notice_days = fields.IntField(default=14)
    
    allows_pets = fields.BooleanField(default=False, index=True)
    allows_smoking = fields.BooleanField(default=False, index=True)
    allows_children = fields.BooleanField(default=True, index=True)
    allows_events = fields.BooleanField(default=False, index=True)
    max_guests = fields.IntField(default=2)
    cleaning_fee = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    security_deposit = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    status = fields.IntEnumField(SwapStatus, default=SwapStatus.DRAFT, index=True)
    is_featured = fields.BooleanField(default=False, index=True)
    is_verified = fields.BooleanField(default=False, index=True)
    
    view_count = fields.IntField(default=0, index=True)
    inquiry_count = fields.IntField(default=0)
    offer_count = fields.IntField(default=0)
    
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    published_at = fields.DatetimeField(null=True, index=True)
    expires_at = fields.DatetimeField(null=True, index=True)
    
    description = fields.TextField()
    house_rules = fields.JSONField(default=list)
    neighborhood_info = fields.TextField(null=True)
    transportation_info = fields.TextField(null=True)
    tags = fields.JSONField(default=list)
    
    class Meta:
        table = "house_swap_listings"
        indexes = [
            ("listing_code",),
            ("owner_id", "status"),
            # ("property_id", "status"),
            ("swap_type", "status"),
            ("available_from", "available_to"),
            ("allows_pets", "status"),
            ("is_featured", "status"),
        ]
        ordering = ["-is_featured", "-created_at"]
    
    @staticmethod
    async def generate_listing_code() -> str:
        """Generate a unique listing code."""
        year = datetime.now().year
        
        while True:
            random_numbers = ''.join(random.choices(string.digits, k=6))
            code = f"SWAP-{year}-{random_numbers}"
            
            exists = await HouseSwapListing.filter(listing_code=code).exists()
            if not exists:
                return code
    
    @staticmethod
    def generate_title(property_data: Dict[str, Any]) -> str:
        """Generate a listing title based on property data."""
        property_type = property_data.get('type', 'Property').title()
        bedrooms = property_data.get('bedrooms', 1)
        location = property_data.get('city', 'Unknown Location')
        
        title_options = [
            f"Beautiful {bedrooms}BR {property_type} in {location} for Swap",
            f"Luxury {property_type} in {location} - Available for Home Exchange",
            f"Modern {bedrooms}-Bedroom {property_type} in {location}",
            f"Stunning {property_type} in Prime {location} Location"
        ]
        
        return random.choice(title_options)
    
    @staticmethod
    def calculate_expiry_date(months: int = 3) -> datetime:
        """Calculate expiry date for listing."""
        return datetime.now() + timedelta(days=months * 30)
    
    @staticmethod
    def get_default_blackout_dates() -> List[str]:
        """Get default blackout dates (e.g., holidays)."""
        current_year = datetime.now().year
        holidays = [
            f"{current_year}-12-24",  # Christmas Eve
            f"{current_year}-12-25",  # Christmas Day
            f"{current_year}-12-31",  # New Year's Eve
            f"{current_year}-01-01",  # New Year's Day
        ]
        return holidays
    
    async def generate_and_set_codes(self):
        """Generate and set all necessary codes and values before saving."""
        if not self.listing_code:
            self.listing_code = await self.generate_listing_code()
        
        if not self.title and self.property:
            property_data = await self.property.to_dict()
            self.title = self.generate_title(property_data)
        
        if not self.expires_at and self.published_at:
            self.expires_at = self.calculate_expiry_date()
        elif not self.expires_at:
            self.expires_at = self.calculate_expiry_date()
        
        if not self.blackout_dates:
            self.blackout_dates = self.get_default_blackout_dates()
        
        if self.max_swap_duration and self.min_swap_duration > self.max_swap_duration:
            self.max_swap_duration = self.min_swap_duration
    
    async def save(self, *args, **kwargs):
        """Override save to generate codes and validate before saving."""
        await self.generate_and_set_codes()
        await self.validate_listing()
        await super().save(*args, **kwargs)
    
    async def validate_listing(self):
        """Validate listing data before saving."""
        if not self.owner_id:
            raise ValueError("Owner is required")
        
        if not self.property_id:
            raise ValueError("Property is required")
        
        if not self.description or len(self.description.strip()) < 50:
            raise ValueError("Description must be at least 50 characters")
        
        if self.min_swap_duration <= 0:
            raise ValueError("Minimum swap duration must be positive")
        
        if self.max_swap_duration and self.max_swap_duration <= 0:
            raise ValueError("Maximum swap duration must be positive")
        
        if self.max_guests <= 0:
            raise ValueError("Maximum guests must be positive")
        
        if self.available_from and self.available_to:
            if self.available_from >= self.available_to:
                raise ValueError("Available from date must be before available to date")
    
    async def publish(self):
        """Publish the listing."""
        if self.status != SwapStatus.DRAFT:
            raise ValueError("Only draft listings can be published")
        
        self.status = SwapStatus.ACTIVE
        self.published_at = datetime.now()
        self.expires_at = self.calculate_expiry_date()
        
        await self.save(update_fields=["status", "published_at", "expires_at"])
    
    async def archive(self):
        """Archive the listing."""
        self.status = SwapStatus.ARCHIVED
        await self.save(update_fields=["status"])
    
    async def expire(self):
        """Mark the listing as expired."""
        if self.status in [SwapStatus.ACTIVE, SwapStatus.PENDING]:
            self.status = SwapStatus.EXPIRED
            await self.save(update_fields=["status"])
    
    async def reserve(self):
        """Mark the listing as reserved."""
        if self.status == SwapStatus.ACTIVE:
            self.status = SwapStatus.RESERVED
            await self.save(update_fields=["status"])
    
    async def confirm_swap(self):
        """Mark the listing as confirmed for swap."""
        self.status = SwapStatus.CONFIRMED
        await self.save(update_fields=["status"])
    
    async def mark_in_progress(self):
        """Mark the listing as swap in progress."""
        self.status = SwapStatus.IN_PROGRESS
        await self.save(update_fields=["status"])
    
    async def complete_swap(self):
        """Mark the listing as swap completed."""
        self.status = SwapStatus.COMPLETED
        await self.save(update_fields=["status"])
    
    async def increment_view(self):
        """Increment view count."""
        self.view_count += 1
        await self.save(update_fields=["view_count"])
    
    async def increment_inquiry(self):
        """Increment inquiry count."""
        self.inquiry_count += 1
        await self.save(update_fields=["inquiry_count"])
    
    async def increment_offer(self):
        """Increment offer count."""
        self.offer_count += 1
        await self.save(update_fields=["offer_count"])
    
    async def verify_listing(self):
        """Verify the listing (admin action)."""
        self.is_verified = True
        await self.save(update_fields=["is_verified"])
    
    async def feature_listing(self):
        """Feature the listing (admin action)."""
        self.is_featured = True
        await self.save(update_fields=["is_featured"])
    
    async def unfeature_listing(self):
        """Remove featured status."""
        self.is_featured = False
        await self.save(update_fields=["is_featured"])
    
    async def add_tag(self, tag: str):
        """Add a tag to the listing."""
        if tag not in self.tags:
            self.tags.append(tag)
            await self.save(update_fields=["tags"])
    
    async def add_blackout_date(self, date_str: str):
        """Add a blackout date."""
        if date_str not in self.blackout_dates:
            self.blackout_dates.append(date_str)
            await self.save(update_fields=["blackout_dates"])
    
    async def remove_blackout_date(self, date_str: str):
        """Remove a blackout date."""
        if date_str in self.blackout_dates:
            self.blackout_dates.remove(date_str)
            await self.save(update_fields=["blackout_dates"])
    
    async def add_desired_location(self, location: str):
        """Add a desired location."""
        if location not in self.desired_locations:
            self.desired_locations.append(location)
            await self.save(update_fields=["desired_locations"])
    
    async def add_house_rule(self, rule: str):
        """Add a house rule."""
        if rule not in self.house_rules:
            self.house_rules.append(rule)
            await self.save(update_fields=["house_rules"])
    
    async def is_available_for_date(self, date_str: str) -> bool:
        """Check if listing is available for a specific date."""
        if date_str in self.blackout_dates:
            return False
        
        if self.availability_type == AvailabilityType.WEEKENDS_ONLY:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_obj.weekday() not in [5, 6]:  # Saturday=5, Sunday=6
                return False
        
        if self.availability_type == AvailabilityType.WEEKDAYS_ONLY:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_obj.weekday() in [5, 6]:  # Saturday=5, Sunday=6
                return False
        
        if self.available_from and date_str < self.available_from.strftime("%Y-%m-%d"):
            return False
        
        if self.available_to and date_str > self.available_to.strftime("%Y-%m-%d"):
            return False
        
        return True
    
    async def get_available_dates(self, start_date: Optional[str] = None, 
                                 end_date: Optional[str] = None) -> List[str]:
        """Get all available dates within a range."""
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        if not end_date:
            end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        available_dates = []
        current = start
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            if await self.is_available_for_date(date_str):
                available_dates.append(date_str)
            current += timedelta(days=1)
        
        return available_dates
    
    @property
    def is_active(self) -> bool:
        """Check if listing is active."""
        return self.status == SwapStatus.ACTIVE
    
    @property
    def is_published(self) -> bool:
        """Check if listing is published."""
        return self.published_at is not None
    
    @property
    def is_expired(self) -> bool:
        """Check if listing has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until listing expires."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)
    
    @property
    def match_score(self) -> Dict[str, Any]:
        """Calculate match score for search ranking."""
        score = 0
        factors = []
        
        if self.is_verified:
            score += 20
            factors.append("verified_listing")
        
        if self.is_featured:
            score += 15
            factors.append("featured_listing")
        
        if self.view_count > 100:
            score += 10
            factors.append("popular")
        
        if self.offer_count > 5:
            score += 5
            factors.append("high_demand")
        
        if len(self.tags) > 3:
            score += 5
            factors.append("well_tagged")
        
        if len(self.description) > 200:
            score += 5
            factors.append("detailed_description")
        
        return {"score": score, "factors": factors}
    
    @classmethod
    async def create_listing(
        cls,
        owner_id: str,
        property_id: str,
        description: str,
        swap_type: SwapType = SwapType.SIMULTANEOUS,
        **kwargs
    ) -> 'HouseSwapListing':
        """Factory method to create a new listing."""
        
        listing = cls(
            owner_id=owner_id,
            property_id=property_id,
            description=description,
            swap_type=swap_type,
            desired_locations=kwargs.get('desired_locations', []),
            desired_property_types=kwargs.get('desired_property_types', []),
            desired_amenities=kwargs.get('desired_amenities', []),
            min_swap_duration=kwargs.get('min_swap_duration', 1),
            max_swap_duration=kwargs.get('max_swap_duration'),
            preferred_duration=kwargs.get('preferred_duration', 7),
            availability_type=kwargs.get('availability_type', AvailabilityType.FLEXIBLE),
            available_from=kwargs.get('available_from'),
            available_to=kwargs.get('available_to'),
            allows_pets=kwargs.get('allows_pets', False),
            allows_smoking=kwargs.get('allows_smoking', False),
            allows_children=kwargs.get('allows_children', True),
            allows_events=kwargs.get('allows_events', False),
            max_guests=kwargs.get('max_guests', 2),
            cleaning_fee=kwargs.get('cleaning_fee'),
            security_deposit=kwargs.get('security_deposit'),
            house_rules=kwargs.get('house_rules', []),
            neighborhood_info=kwargs.get('neighborhood_info'),
            transportation_info=kwargs.get('transportation_info'),
            tags=kwargs.get('tags', [])
        )
        
        await listing.save()
        return listing
    
    @classmethod
    async def search_listings(
        cls,
        location: Optional[str] = None,
        swap_type: Optional[SwapType] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        allows_pets: Optional[bool] = None,
        allows_children: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List['HouseSwapListing']:
        """Search for listings with filters."""
        query = cls.filter(status=SwapStatus.ACTIVE)
        
        if location:
            query = query.filter(desired_locations__contains=[location])
        
        if swap_type:
            query = query.filter(swap_type=swap_type)
        
        if min_duration:
            query = query.filter(min_swap_duration__lte=min_duration)
        
        if max_duration:
            query = query.filter(
                fields.Q(max_swap_duration__isnull=True) | 
                fields.Q(max_swap_duration__gte=max_duration)
            )
        
        if allows_pets is not None:
            query = query.filter(allows_pets=allows_pets)
        
        if allows_children is not None:
            query = query.filter(allows_children=allows_children)
        
        return await query.order_by("-is_featured", "-created_at").offset(offset).limit(limit).all()
    
    @classmethod
    async def get_user_listings(
        cls,
        user_id: str,
        status: Optional[SwapStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List['HouseSwapListing']:
        """Get all listings for a user."""
        query = cls.filter(owner_id=user_id)
        
        if status:
            query = query.filter(status=status)
        
        return await query.order_by("-created_at").offset(offset).limit(limit).all()
    
    @classmethod
    async def cleanup_expired_listings(cls):
        """Clean up expired listings."""
        expired_listings = await cls.filter(
            status__in=[SwapStatus.ACTIVE, SwapStatus.PENDING],
            expires_at__lt=datetime.now()
        ).all()
        
        for listing in expired_listings:
            await listing.expire()
        
        return len(expired_listings)