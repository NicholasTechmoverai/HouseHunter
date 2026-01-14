from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import IntEnum
import random
import string
import hashlib


class SwapAgreementStatus(IntEnum):
    DRAFT = 1
    PENDING_SIGNATURES = 2
    SIGNED = 3
    ACTIVE = 4
    COMPLETED = 5
    CANCELLED = 6
    DISPUTED = 7


class SwapAgreement(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    agreement_code = fields.CharField(max_length=50, unique=True, index=True)
    
    originating_offer = fields.OneToOneField(
        'models.SwapOffer',
        related_name='agreement',
        on_delete=fields.CASCADE,
        index=True
    )
    
    party_a = fields.ForeignKeyField(
        'models.User',
        related_name='swap_agreements_as_party_a',
        on_delete=fields.CASCADE,
        index=True
    )
    
    party_b = fields.ForeignKeyField(
        'models.User',
        related_name='swap_agreements_as_party_b',
        on_delete=fields.CASCADE,
        index=True
    )
    
    property_a = fields.ForeignKeyField(
        'models.HouseSwapListing',
        related_name='swap_agreements_as_property_a',
        on_delete=fields.CASCADE,
        index=True
    )
    
    property_b = fields.ForeignKeyField(
        'models.HouseSwapListing',
        related_name='swap_agreements_as_property_b',
        on_delete=fields.CASCADE,
        index=True
    )
    
    start_date = fields.DateField(index=True)
    end_date = fields.DateField(index=True)
    total_days = fields.IntField()
    
    monetary_exchange = fields.BooleanField(default=False)
    amount = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    security_deposit_amount = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    status = fields.IntEnumField(SwapAgreementStatus, default=SwapAgreementStatus.DRAFT, index=True)
    
    party_a_signed_at = fields.DatetimeField(null=True)
    party_b_signed_at = fields.DatetimeField(null=True)
    fully_signed_at = fields.DatetimeField(null=True)
    
    insurance_provided = fields.BooleanField(default=False)
    insurance_details = fields.JSONField(null=True)
    
    platform_fee = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    platform_fee_paid = fields.BooleanField(default=False)
    
    agreement_document_url = fields.TextField(null=True)
    terms_accepted = fields.JSONField(default=list)
    
    cancellation_reason = fields.TextField(null=True)
    cancellation_initiated_by = fields.ForeignKeyField(
        'models.User',
        related_name='cancelled_swap_agreements',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    completed_at = fields.DatetimeField(null=True)
    completion_notes = fields.TextField(null=True)
    
    rating_by_a_to_b = fields.IntField(null=True)
    rating_by_b_to_a = fields.IntField(null=True)
    review_by_a = fields.TextField(null=True)
    review_by_b = fields.TextField(null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "swap_agreements"
        indexes = [
            ("agreement_code",),
            ("party_a_id", "status"),
            ("party_b_id", "status"),
            ("start_date", "end_date"),
            ("status", "start_date"),
        ]
        ordering = ["-created_at"]
    
    @staticmethod
    async def generate_agreement_code(offer_code: str) -> str:
        """Generate a unique agreement code based on offer code."""
        year = datetime.now().year
        
        offer_hash = hashlib.md5(offer_code.encode()).hexdigest()[:6].upper()
        
        while True:
            random_chars = ''.join(random.choices(string.ascii_uppercase, k=2))
            code = f"AGR-{year}-{offer_hash}-{random_chars}"
            
            exists = await SwapAgreement.filter(agreement_code=code).exists()
            if not exists:
                return code
    
    @staticmethod
    def calculate_total_days(start_date: datetime, end_date: datetime) -> int:
        """Calculate total days between start and end dates."""
        return (end_date - start_date).days
    
    @staticmethod
    def calculate_platform_fee(total_amount: float, fee_percentage: float = 5.0) -> float:
        """Calculate platform fee based on transaction amount."""
        if not total_amount or total_amount <= 0:
            return 0.0
        return round(total_amount * (fee_percentage / 100), 2)
    
    async def generate_and_set_codes(self):
        """Generate and set all necessary codes and values before saving."""
        if not self.agreement_code and self.originating_offer:
            self.agreement_code = await self.generate_agreement_code(
                self.originating_offer.offer_code
            )
        
        if not self.total_days and self.start_date and self.end_date:
            self.total_days = self.calculate_total_days(self.start_date, self.end_date)
        
        if not self.platform_fee and self.amount:
            self.platform_fee = self.calculate_platform_fee(float(self.amount))
        
        if self.status == SwapAgreementStatus.DRAFT:
            if self.party_a_signed_at or self.party_b_signed_at:
                self.status = SwapAgreementStatus.PENDING_SIGNATURES
    
    async def save(self, *args, **kwargs):
        """Override save to generate codes and validate before saving."""
        await self.generate_and_set_codes()
        await self.validate_agreement()
        await super().save(*args, **kwargs)
    
    async def validate_agreement(self):
        """Validate agreement data before saving."""
        if not self.originating_offer_id:
            raise ValueError("Originating offer is required")
        
        if not self.party_a_id or not self.party_b_id:
            raise ValueError("Both parties are required")
        
        if self.party_a_id == self.party_b_id:
            raise ValueError("Parties must be different users")
        
        if not self.property_a_id or not self.property_b_id:
            raise ValueError("Both properties are required")
        
        if self.property_a_id == self.property_b_id:
            raise ValueError("Properties must be different")
        
        if not self.start_date or not self.end_date:
            raise ValueError("Start and end dates are required")
        
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        
        if self.start_date < datetime.now().date():
            raise ValueError("Start date cannot be in the past")
        
        if self.monetary_exchange and not self.amount:
            raise ValueError("Amount is required for monetary exchange")
    
    async def sign(self, party_id: str):
        """Sign the agreement for a specific party."""
        if party_id == self.party_a_id and not self.party_a_signed_at:
            self.party_a_signed_at = datetime.now()
        elif party_id == self.party_b_id and not self.party_b_signed_at:
            self.party_b_signed_at = datetime.now()
        else:
            raise ValueError("Invalid party or already signed")
        
        if self.party_a_signed_at and self.party_b_signed_at:
            self.fully_signed_at = datetime.now()
            self.status = SwapAgreementStatus.SIGNED
        else:
            self.status = SwapAgreementStatus.PENDING_SIGNATURES
        
        await self.save(update_fields=[
            "party_a_signed_at", "party_b_signed_at", 
            "fully_signed_at", "status"
        ])
    
    async def activate(self):
        """Activate the agreement (swap period begins)."""
        if self.status != SwapAgreementStatus.SIGNED:
            raise ValueError("Agreement must be signed before activation")
        
        if self.start_date > datetime.now().date():
            raise ValueError("Cannot activate before start date")
        
        self.status = SwapAgreementStatus.ACTIVE
        await self.save(update_fields=["status"])
    
    async def complete(self, notes: Optional[str] = None):
        """Mark the agreement as completed."""
        if self.status != SwapAgreementStatus.ACTIVE:
            raise ValueError("Agreement must be active to complete")
        
        if self.end_date > datetime.now().date():
            raise ValueError("Cannot complete before end date")
        
        self.status = SwapAgreementStatus.COMPLETED
        self.completed_at = datetime.now()
        self.completion_notes = notes
        await self.save(update_fields=["status", "completed_at", "completion_notes"])
    
    async def cancel(self, reason: str, initiator_id: str):
        """Cancel the agreement."""
        if self.status in [SwapAgreementStatus.COMPLETED, SwapAgreementStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel agreement in {self.status} status")
        
        self.status = SwapAgreementStatus.CANCELLED
        self.cancellation_reason = reason
        self.cancellation_initiated_by_id = initiator_id
        await self.save(update_fields=[
            "status", "cancellation_reason", "cancellation_initiated_by_id"
        ])
    
    async def dispute(self):
        """Mark the agreement as disputed."""
        if self.status not in [SwapAgreementStatus.ACTIVE, SwapAgreementStatus.SIGNED]:
            raise ValueError("Cannot dispute agreement in current status")
        
        self.status = SwapAgreementStatus.DISPUTED
        await self.save(update_fields=["status"])
    
    async def add_rating(self, from_party_id: str, rating: int, review: Optional[str] = None):
        """Add a rating and review from one party to another."""
        if self.status != SwapAgreementStatus.COMPLETED:
            raise ValueError("Can only rate completed agreements")
        
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        if from_party_id == self.party_a_id:
            self.rating_by_a_to_b = rating
            self.review_by_a = review
        elif from_party_id == self.party_b_id:
            self.rating_by_b_to_a = rating
            self.review_by_b = review
        else:
            raise ValueError("Invalid party")
        
        await self.save(update_fields=[
            "rating_by_a_to_b", "rating_by_b_to_a",
            "review_by_a", "review_by_b"
        ])
    
    async def calculate_average_rating(self) -> Optional[float]:
        """Calculate average rating from both parties."""
        ratings = []
        if self.rating_by_a_to_b:
            ratings.append(self.rating_by_a_to_b)
        if self.rating_by_b_to_a:
            ratings.append(self.rating_by_b_to_a)
        
        if not ratings:
            return None
        
        return sum(ratings) / len(ratings)
    
    async def pay_platform_fee(self):
        """Mark platform fee as paid."""
        self.platform_fee_paid = True
        await self.save(update_fields=["platform_fee_paid"])
    
    @property
    def is_signed(self) -> bool:
        """Check if agreement is fully signed."""
        return self.status == SwapAgreementStatus.SIGNED
    
    @property
    def is_active(self) -> bool:
        """Check if agreement is currently active."""
        today = datetime.now().date()
        return (
            self.status == SwapAgreementStatus.ACTIVE and
            self.start_date <= today <= self.end_date
        )
    
    @property
    def is_completed(self) -> bool:
        """Check if agreement is completed."""
        return self.status == SwapAgreementStatus.COMPLETED
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining in agreement."""
        today = datetime.now().date()
        if today < self.start_date:
            return self.total_days
        elif today > self.end_date:
            return 0
        else:
            return (self.end_date - today).days
    
    @property
    def days_elapsed(self) -> int:
        """Get days elapsed in agreement."""
        today = datetime.now().date()
        if today < self.start_date:
            return 0
        elif today > self.end_date:
            return self.total_days
        else:
            return (today - self.start_date).days
    
    @property
    def progress_percentage(self) -> float:
        """Get progress percentage of agreement."""
        if self.total_days == 0:
            return 0.0
        return (self.days_elapsed / self.total_days) * 100
    
    @classmethod
    async def create_from_offer(
        cls,
        offer: 'SwapOffer',
        start_date: datetime,
        end_date: datetime,
        security_deposit_amount: Optional[float] = None,
        insurance_provided: bool = False,
        insurance_details: Optional[Dict] = None
    ) -> 'SwapAgreement':
        """Factory method to create agreement from an offer."""
        
        agreement = cls(
            originating_offer=offer,
            party_a=offer.from_user,
            party_b=offer.to_user,
            property_a=offer.offering_listing.property,
            property_b=offer.target_listing.property,
            start_date=start_date,
            end_date=end_date,
            total_days=cls.calculate_total_days(start_date, end_date),
            monetary_exchange=bool(offer.proposed_rent),
            amount=offer.proposed_rent,
            security_deposit_amount=security_deposit_amount or offer.proposed_security_deposit,
            insurance_provided=insurance_provided,
            insurance_details=insurance_details,
            platform_fee=cls.calculate_platform_fee(
                float(offer.proposed_rent) if offer.proposed_rent else 0
            ),
            status=SwapAgreementStatus.DRAFT
        )
        
        await agreement.save()
        return agreement
    
    @classmethod
    async def get_user_agreements(
        cls,
        user_id: str,
        status: Optional[SwapAgreementStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List['SwapAgreement']:
        """Get all agreements for a user."""
        query = cls.filter(
            fields.Q(party_a_id=user_id) | fields.Q(party_b_id=user_id)
        )
        
        if status:
            query = query.filter(status=status)
        
        return await query.order_by("-created_at").offset(offset).limit(limit).all()
    
    @classmethod
    async def get_active_agreements(cls) -> List['SwapAgreement']:
        """Get all currently active agreements."""
        today = datetime.now().date()
        
        return await cls.filter(
            status=SwapAgreementStatus.ACTIVE,
            start_date__lte=today,
            end_date__gte=today
        ).all()
    
    @classmethod
    async def get_agreements_needing_activation(cls) -> List['SwapAgreement']:
        """Get signed agreements that need to be activated."""
        today = datetime.now().date()
        
        return await cls.filter(
            status=SwapAgreementStatus.SIGNED,
            start_date__lte=today
        ).all()
    
    @classmethod
    async def get_agreements_needing_completion(cls) -> List['SwapAgreement']:
        """Get active agreements that need to be completed."""
        today = datetime.now().date()
        
        return await cls.filter(
            status=SwapAgreementStatus.ACTIVE,
            end_date__lt=today
        ).all()
    
    async def generate_agreement_document(self) -> str:
        """Generate agreement document URL (placeholder implementation)."""
        document_hash = hashlib.md5(
            f"{self.agreement_code}{datetime.now().timestamp()}".encode()
        ).hexdigest()
        
        self.agreement_document_url = f"/agreements/{self.agreement_code}/{document_hash}.pdf"
        await self.save(update_fields=["agreement_document_url"])
        
        return self.agreement_document_url