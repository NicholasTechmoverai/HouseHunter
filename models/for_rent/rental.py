from tortoise import fields
from tortoise.models import Model
from enum import Enum
from decimal import Decimal
from datetime import datetime
import random
import re

from models.defaults.property_catogories import PropertyCategory
from .rules import RentalRules
from .amenities import RentalAmenity
from .gallery import RentalGallery

related_fields = {
    "user": "models.User",
    "amenities": "models.RentalAmenity",
    "rules": "models.RentalRules",
    "gallery": "models.RentalGallery",
    "pricing": "models.RentalPricing",
    "admin_user": "models.AdminUser",
}

class RentalStatus(str, Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    UNDER_MAINTENANCE = "under_maintenance"
    RESERVED = "reserved"
    RENTED = "rented"
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"

class RentalComplex(Model):
    id = fields.CharField(pk=True, max_length=36)
    public_id = fields.CharField(max_length=36, unique=True, index=True)
    
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=255, unique=True, index=True, null=True)
    description = fields.TextField()
    profile_picture = fields.CharField(max_length=500, null=True)
    theme_color = fields.CharField(max_length=7, default="#FFFFFF")
    year_built = fields.IntField(null=True)
    
    lot_size = fields.IntField(null=True)
    floor_number = fields.SmallIntField(null=True)
    
    country = fields.CharField(max_length=100, null=True)
    county = fields.CharField(max_length=100, null=True)
    state = fields.CharField(max_length=100, null=True)
    city = fields.CharField(max_length=100, null=True)
    zip_code = fields.CharField(max_length=20, null=True)
    address = fields.TextField(null=True)
    latitude = fields.FloatField(null=True, index=True)
    longitude = fields.FloatField(null=True, index=True)
    contact_number = fields.CharField(max_length=20, null=True)
    
    category = fields.IntEnumField(PropertyCategory, default=PropertyCategory.APARTMENT)
    
    publisher = fields.ForeignKeyField(
        related_fields["user"],
        related_name="owned_rentals",
        on_delete=fields.CASCADE
    )
    pricing = fields.ForeignKeyField(
        "models.RentalPricing",
        related_name="rentals",
        null=True,
        on_delete=fields.CASCADE
    )
 

    amenities: fields.ReverseRelation["RentalAmenity"]
    rules: fields.ReverseRelation["RentalRules"]
    gallery: fields.ReverseRelation["RentalGallery"]


    managers = fields.ManyToManyField(
        related_fields["user"],
        related_name="managed_rentals",
        through="rental_managers",
        on_delete=fields.CASCADE
    )
    
    price = fields.DecimalField(max_digits=12, decimal_places=2, null=True)
    bedrooms = fields.IntField(default=1)
    bathrooms = fields.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    area_sqft = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    is_available = fields.BooleanField(default=True, index=True)
    available_from = fields.DatetimeField(null=True)
    status = fields.CharEnumField(RentalStatus, default=RentalStatus.DRAFT, index=True)
    
    is_featured = fields.BooleanField(default=False, index=True)
    is_verified = fields.BooleanField(default=False, index=True)
    is_deleted = fields.BooleanField(default=False, index=True)
    
    verified_by = fields.ForeignKeyField(
        related_fields["admin_user"],
        related_name="verified_rentals",
        null=True,
        on_delete=fields.SET_NULL
    )
    
    verified_at = fields.DatetimeField(null=True)
    deleted_at = fields.DatetimeField(null=True)
    rejection_reason = fields.TextField(null=True)
    search_vector = fields.TextField(null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "rentals"
        indexes = [
            ("city", "price"),
            ("city", "category", "is_available"),
            ("price", "bedrooms"),
            ("created_at",),
            ("is_featured", "is_available"),
            ("status", "is_available"),
            ("slug",),
        ]
        ordering = ["-created_at"]

    @staticmethod
    async def generate_unique_id():
        while True:
            new_id = f"RNT-{random.randint(100000, 999999)}"
            exists = await RentalComplex.filter(public_id=new_id).exists()
            if not exists:
                return new_id

    @staticmethod
    def generate_slug(title: str) -> str:
        base_slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        base_slug = re.sub(r'[-\s]+', '-', base_slug)
        return base_slug

    async def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = await self.generate_unique_id()
        
        if self.title and not self.slug:
            base_slug = self.generate_slug(self.title)
            counter = 1
            slug = base_slug
            while await RentalComplex.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        await super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    async def get_location_summary(self) -> dict:
        return {
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            } if self.latitude and self.longitude else None
        }
    
    async def get_property_summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "category": self.category.value,
            "bedrooms": self.bedrooms,
            "bathrooms": float(self.bathrooms),
            "area_sqft": float(self.area_sqft) if self.area_sqft else None,
            "price": float(self.price) if self.price else None,
            "status": self.status.value,
            "is_available": self.is_available,
            "is_verified": self.is_verified,
            "is_featured": self.is_featured,
            "year_built": self.year_built,
            "profile_picture": self.profile_picture,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    async def to_dict(self) -> dict:
        return {
            "id": self.id,
            "public_id": self.public_id,
            "title": self.title,
            "slug": self.slug,
            "category": self.category.value,
            "description": self.description,
            "profile_picture": self.profile_picture,
            "theme_color": self.theme_color,
            "year_built": self.year_built,
            "lot_size": self.lot_size,
            "floor_number": self.floor_number,
            "country": self.country,
            "county": self.county,
            "state": self.state,
            "city": self.city,
            "zip_code": self.zip_code,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "contact_number": self.contact_number,
            "bedrooms": self.bedrooms,
            "bathrooms": float(self.bathrooms),
            "area_sqft": float(self.area_sqft) if self.area_sqft else None,
            "price": float(self.price) if self.price else None,
            "is_available": self.is_available,
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "status": self.status.value,
            "is_featured": self.is_featured,
            "is_verified": self.is_verified,
            "is_deleted": self.is_deleted,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }