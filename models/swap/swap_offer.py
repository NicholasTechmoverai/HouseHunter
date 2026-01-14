from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import IntEnum
import random
import string


class SwapOfferStatus(IntEnum):
    PENDING = 1
    ACCEPTED = 2
    COUNTER_OFFER = 3
    REJECTED = 4
    EXPIRED = 5
    WITHDRAWN = 6
    CONFIRMED = 7
    CANCELLED = 8


class SwapOffer(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    offer_code = fields.CharField(max_length=50, unique=True, index=True,default=None,null=True)
    
    target_listing = fields.ForeignKeyField(
        'models.HouseSwapListing',
        related_name='received_offers',
        on_delete=fields.CASCADE,
        index=True
    )
    
    offering_listing = fields.ForeignKeyField(
        'models.HouseSwapListing',
        related_name='sent_offers',
        on_delete=fields.CASCADE,
        index=True
    )
    
    from_user = fields.ForeignKeyField(
        'models.User',
        related_name='sent_swap_offers',
        on_delete=fields.CASCADE,
        index=True
    )
    
    to_user = fields.ForeignKeyField(
        'models.User',
        related_name='received_swap_offers',
        on_delete=fields.CASCADE,
        index=True
    )
    
    proposed_start_date = fields.DateField(index=True)
    proposed_end_date = fields.DateField(index=True)
    proposed_duration = fields.IntField()
    
    status = fields.IntEnumField(SwapOfferStatus, default=lambda: SwapOfferStatus.PENDING, index=True)
    message = fields.TextField(null=True)
    special_requests = fields.JSONField(default=list)
    
    proposed_rent = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    proposed_cleaning_fee = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    proposed_security_deposit = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    responded_at = fields.DatetimeField(null=True)
    response_message = fields.TextField(null=True)
    
    counter_to_offer = fields.ForeignKeyField(
        'models.SwapOffer',
        related_name='counter_offers',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    expires_at = fields.DatetimeField(null=True, index=True)
    
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "swap_offers"
        indexes = [
            ("offer_code",),
            ("from_user_id", "status"),
            ("to_user_id", "status"),
            ("target_listing_id", "status"),
            ("proposed_start_date", "proposed_end_date"),
            ("expires_at", "status"),
        ]
        ordering = ["-created_at"]
    
    @staticmethod
    async def generate_offer_code() -> str:
        """Generate a unique offer code."""
        year = datetime.now().year
        while True:
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"OFFER-{year}-{random_chars}"
            
            exists = await SwapOffer.filter(offer_code=code).exists()
            if not exists:
                return code
    
    @staticmethod
    def calculate_expiry_date(days: int = 7) -> datetime:
        """Calculate expiry date for an offer."""
        return datetime.now() + timedelta(days=days)
    
    @staticmethod
    def calculate_duration(start_date: datetime, end_date: datetime) -> int:
        """Calculate duration in days between two dates."""
        return (end_date - start_date).days
    
    async def generate_and_set_codes(self):
        """Generate and set all necessary codes and values before saving."""
        if not self.offer_code:
            self.offer_code = await self.generate_offer_code()
        
        if not self.expires_at:
            self.expires_at = self.calculate_expiry_date()
        
        if not self.proposed_duration and self.proposed_start_date and self.proposed_end_date:
            self.proposed_duration = self.calculate_duration(
                self.proposed_start_date, 
                self.proposed_end_date
            )
    
    async def save(self, *args, **kwargs):
        """Override save to generate codes and validate before saving."""
        await self.generate_and_set_codes()
        await self.validate_offer()
        await super().save(*args, **kwargs)
    
    async def validate_offer(self):
        """Validate offer data before saving."""
        if not self.target_listing_id:
            raise ValueError("Target listing is required")
        
        if not self.offering_listing_id:
            raise ValueError("Offering listing is required")
        
        if not self.from_user_id:
            raise ValueError("From user is required")
        
        if not self.to_user_id:
            raise ValueError("To user is required")
        
        if not self.proposed_start_date or not self.proposed_end_date:
            raise ValueError("Proposed dates are required")
        
        if self.proposed_start_date >= self.proposed_end_date:
            raise ValueError("Start date must be before end date")
        
        duration = self.calculate_duration(self.proposed_start_date, self.proposed_end_date)
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        if self.from_user_id == self.to_user_id:
            raise ValueError("Cannot make an offer to yourself")
    
    async def accept(self, response_message: Optional[str] = None):
        """Accept the swap offer."""
        self.status = SwapOfferStatus.ACCEPTED
        self.responded_at = datetime.now()
        self.response_message = response_message
        await self.save(update_fields=["status", "responded_at", "response_message"])
    
    async def reject(self, response_message: Optional[str] = None):
        """Reject the swap offer."""
        self.status = SwapOfferStatus.REJECTED
        self.responded_at = datetime.now()
        self.response_message = response_message
        await self.save(update_fields=["status", "responded_at", "response_message"])
    
    async def withdraw(self):
        """Withdraw the swap offer."""
        self.status = SwapOfferStatus.WITHDRAWN
        await self.save(update_fields=["status"])
    
    async def create_counter_offer(self, **kwargs) -> 'SwapOffer':
        """Create a counter offer based on this offer."""
        counter_offer = await SwapOffer.create(
            target_listing=self.target_listing,
            offering_listing=self.offering_listing,
            from_user=self.to_user,
            to_user=self.from_user,
            proposed_start_date=kwargs.get('proposed_start_date', self.proposed_start_date),
            proposed_end_date=kwargs.get('proposed_end_date', self.proposed_end_date),
            proposed_rent=kwargs.get('proposed_rent', self.proposed_rent),
            proposed_cleaning_fee=kwargs.get('proposed_cleaning_fee', self.proposed_cleaning_fee),
            proposed_security_deposit=kwargs.get('proposed_security_deposit', self.proposed_security_deposit),
            message=kwargs.get('message'),
            special_requests=kwargs.get('special_requests', self.special_requests.copy()),
            counter_to_offer=self,
            status=SwapOfferStatus.PENDING
        )
        
        self.status = SwapOfferStatus.COUNTER_OFFER
        await self.save(update_fields=["status"])
        
        return counter_offer
    
    async def confirm(self):
        """Confirm the swap offer (both parties agreed)."""
        self.status = SwapOfferStatus.CONFIRMED
        await self.save(update_fields=["status"])
    
    async def expire(self):
        """Mark the offer as expired."""
        if self.status == SwapOfferStatus.PENDING:
            self.status = SwapOfferStatus.EXPIRED
            await self.save(update_fields=["status"])
    
    @property
    def is_expired(self) -> bool:
        """Check if the offer has expired."""
        if self.expires_at and datetime.now() > self.expires_at:
            return True
        return False
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until offer expires."""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)
    
    @property
    def is_active(self) -> bool:
        """Check if offer is still active (not expired or finalized)."""
        active_statuses = [SwapOfferStatus.PENDING, SwapOfferStatus.COUNTER_OFFER]
        return self.status in active_statuses and not self.is_expired
    
    @classmethod
    async def create_offer(
        cls,
        target_listing_id: str,
        offering_listing_id: str,
        from_user_id: str,
        to_user_id: str,
        proposed_start_date: datetime,
        proposed_end_date: datetime,
        message: Optional[str] = None,
        **kwargs
    ) -> 'SwapOffer':
        """Factory method to create a new swap offer with validation."""
        
        offer = cls(
            target_listing_id=target_listing_id,
            offering_listing_id=offering_listing_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            proposed_start_date=proposed_start_date,
            proposed_end_date=proposed_end_date,
            message=message,
            proposed_rent=kwargs.get('proposed_rent'),
            proposed_cleaning_fee=kwargs.get('proposed_cleaning_fee'),
            proposed_security_deposit=kwargs.get('proposed_security_deposit'),
            special_requests=kwargs.get('special_requests', []),
            status=SwapOfferStatus.PENDING
        )
        
        await offer.save()
        return offer
    
    @classmethod
    async def get_user_pending_offers(cls, user_id: str) -> List['SwapOffer']:
        """Get all pending offers for a user."""
        return await cls.filter(
            to_user_id=user_id,
            status=SwapOfferStatus.PENDING
        ).prefetch_related('from_user', 'target_listing', 'offering_listing').all()
    
    @classmethod
    async def get_user_sent_offers(cls, user_id: str) -> List['SwapOffer']:
        """Get all offers sent by a user."""
        return await cls.filter(
            from_user_id=user_id
        ).prefetch_related('to_user', 'target_listing', 'offering_listing').all()
    
    @classmethod
    async def cleanup_expired_offers(cls):
        """Clean up expired offers."""
        expired_offers = await cls.filter(
            status=SwapOfferStatus.PENDING,
            expires_at__lt=datetime.now()
        ).all()
        
        for offer in expired_offers:
            await offer.expire()
                    
        return len(expired_offers)