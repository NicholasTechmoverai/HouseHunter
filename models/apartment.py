from enum import Enum
from uuid import uuid4
from tortoise import fields, Model

class ApartmentStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"

class ApartmentType(str, Enum):
    STUDIO = "studio"
    APARTMENT = "apartment"
    PENTHOUSE = "penthouse"
    LOFT = "loft"
    DUPLEX = "duplex"

class Apartment(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=200)
    description = fields.TextField()
    price = fields.FloatField()
    type = fields.CharEnumField(ApartmentType, default=ApartmentType.APARTMENT)
    bedrooms = fields.IntField(default=1)
    bathrooms = fields.IntField(default=1)
    area = fields.FloatField(null=True)
    address = fields.TextField()
    city = fields.CharField(max_length=100)
    
    amenities = fields.JSONField(default=list)  # list of strings
    images = fields.JSONField(default=list)     # list of dicts (url, caption, is_primary)
    
    is_featured = fields.BooleanField(default=False, index=True)
    feature_priority = fields.IntField(null=True)
    is_deleted = fields.BooleanField(default=False, index=True)
    
    latitude = fields.FloatField(null=True)
    longitude = fields.FloatField(null=True)
    
    view_count = fields.IntField(default=0)
    favorite_count = fields.IntField(default=0)
    
    owner = fields.ForeignKeyField("models.User", related_name="apartments", on_delete=fields.CASCADE)
    created_by = fields.ForeignKeyField("models.User", related_name="created_apartments", on_delete=fields.CASCADE)
    
    status = fields.CharEnumField(ApartmentStatus, default=ApartmentStatus.PENDING, index=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    published_at = fields.DatetimeField(null=True)
    
    approved_by = fields.ForeignKeyField("models.User", related_name="approved_apartments", null=True, on_delete=fields.SET_NULL)
    approved_at = fields.DatetimeField(null=True)

    class Meta:
        table = "apartments"
        ordering = ["-created_at"]
