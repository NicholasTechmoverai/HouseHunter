from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator, RegexValidator
import uuid
from enum import IntEnum
from datetime import datetime

from user import BaseUser,TimestampMixin,SoftDeleteMixin

class VerificationStatus(IntEnum):
    PENDING = 0
    VERIFIED = 1
    REJECTED = 2
    EXPIRED = 3
    SUSPENDED = 4
    UNDER_REVIEW = 5


class RentalProviderProfile(Model):
    user = fields.OneToOneField(
        "models.User",
        pk=True,
        related_name="provider_profile",
        on_delete=fields.CASCADE
    )

    business_name = fields.CharField(max_length=255, null=True)
    business_description = fields.TextField(null=True)
    business_phone = fields.CharField(max_length=15, null=True)
    business_email = fields.CharField(max_length=255, null=True)
    
    # Verification and compliance
    verification_status = fields.IntEnumField(VerificationStatus, default=VerificationStatus.PENDING)
    verified_at = fields.DatetimeField(null=True)
    verification_notes = fields.TextField(null=True)
    
    # Identity verification documents
    identity_documents = fields.ManyToManyField(
        'models.IdentityDocument',
        related_name='rental_providers',
        through='provider_documents'
    )
    
    # Business details
    tax_identification_number = fields.CharField(max_length=100, null=True, unique=True)
    business_registration_number = fields.CharField(max_length=100, null=True, unique=True)
    
    # Address information
    business_address = fields.JSONField(default={
        "street": "",
        "city": "",
        "state": "",
        "postal_code": "",
        "country": ""
    })
    
    # Business preferences
    business_preferences = fields.JSONField(default={
        "auto_approve_bookings": False,
        "instant_booking": True,
        "advance_notice_hours": 24
    })
    
    # Statistics (denormalized for performance)
    total_properties = fields.IntField(default=0)
    total_bookings = fields.IntField(default=0)
    average_rating = fields.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Relationships
    properties = fields.ReverseRelation['models.RentalProperty']
    bank_accounts = fields.ReverseRelation['models.BankAccount']
    
    class Meta:
        table = "rental_providers"
        indexes = [
            ("business_name",),
            ("verification_status",),
            ("tax_identification_number",),
            ("business_registration_number",),
            ("is_deleted",)
        ]
    
    @property
    def is_fully_verified(self) -> bool:
        return (
            self.verification_status == VerificationStatus.VERIFIED and
            self.email_verified and
            self.phone_verified
        )
    
    async def update_statistics(self):
        from tortoise.expressions import Count, Avg
        from models.rental_property import RentalProperty
        from models.booking import Booking
        
        self.total_properties = await RentalProperty.filter(
            provider=self, 
            is_deleted=False
        ).count()
        
        self.total_bookings = await Booking.filter(
            property__provider=self,
            status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
        ).count()
        
        # Update average rating
        avg_rating = await Review.filter(
            property__provider=self
        ).annotate(avg_rating=Avg('rating')).values_list('avg_rating', flat=True)
        
        self.average_rating = avg_rating[0] if avg_rating else 0.0
        await self.save()
