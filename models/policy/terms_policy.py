from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import IntEnum

from .index import PolicyAudience,PolicyStatus,PolicyRegion,PolicyLanguage,PolicyType
    
    
class PolicyDocument(Model):
    """
    Main policy document model.
    Stores the actual policy content and metadata.
    """
    
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    policy_code = fields.CharField(max_length=50, unique=True, index=True)  # e.g., "PRIVACY-2024-001"
    title = fields.CharField(max_length=200)
    short_title = fields.CharField(max_length=100, null=True)
    
    policy_type = fields.IntEnumField(PolicyType, index=True)
    version = fields.CharField(max_length=20, default="1.0")  # Semantic versioning
    version_number = fields.IntField(default=1, index=True)
    
    content = fields.TextField()  # HTML or Markdown content
    summary = fields.TextField(null=True)  # Short summary for users
    changelog = fields.TextField(null=True)  # What changed in this version
    
    audience = fields.IntEnumField(PolicyAudience, default=PolicyAudience.ALL_USERS, index=True)
    regions = fields.JSONField(default=list)  # List of PolicyRegion values
    languages = fields.JSONField(default=["en"])  # List of language codes
    
    status = fields.IntEnumField(PolicyStatus, default=PolicyStatus.DRAFT, index=True)
    effective_date = fields.DateField(index=True)  # When policy becomes active
    expiration_date = fields.DateField(null=True, index=True)  # When policy expires
    review_frequency = fields.CharField(max_length=50, default="annual")  # annual, quarterly, etc.
    next_review_date = fields.DateField(null=True, index=True)
    
    is_mandatory = fields.BooleanField(default=True, index=True) 
    min_age_requirement = fields.IntField(null=True)  # Minimum age to accept (e.g., 13, 16, 18)
    requires_explicit_consent = fields.BooleanField(default=False)
    
    published_by = fields.ForeignKeyField(
        'models.User',
        related_name='published_policies',
        null=True,
        on_delete=fields.SET_NULL
    )
    approved_by = fields.ForeignKeyField(
        'models.User',
        related_name='approved_policies',
        null=True,
        on_delete=fields.SET_NULL
    )
    legal_review_by = fields.ForeignKeyField(
        'models.User',
        related_name='legally_reviewed_policies',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    # Previous version reference
    previous_version = fields.ForeignKeyField(
        'models.PolicyDocument',
        related_name='next_versions',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    # Related documents
    related_policies = fields.JSONField(default=list)  # List of related policy codes
    
    # Compliance
    compliance_standards = fields.JSONField(default=list)  # e.g., ["GDPR", "CCPA", "ISO27001"]
    risk_level = fields.CharField(max_length=20, default="medium")  # low, medium, high
    
    # Metrics
    view_count = fields.IntField(default=0, index=True)
    accept_count = fields.IntField(default=0, index=True)
    decline_count = fields.IntField(default=0)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    published_at = fields.DatetimeField(null=True, index=True)
    archived_at = fields.DatetimeField(null=True)
    
    # Metadata
    metadata = fields.JSONField(default=dict)
    tags = fields.JSONField(default=list)
    
    class Meta:
        table = "policy_documents"
        indexes = [
            ("policy_code",),
            ("policy_type", "status"),
            ("policy_type", "effective_date"),
            ("status", "effective_date"),
            ("audience", "status"),
            ("version_number", "policy_type"),
            ("effective_date", "expiration_date"),
        ]
        ordering = ["-effective_date", "-version_number"]
    
    @property
    def is_active(self) -> bool:
        """Check if policy is currently active"""
        today = datetime.utcnow().date()
        
        if self.status != PolicyStatus.ACTIVE:
            return False
        
        if self.effective_date and today < self.effective_date:
            return False
        
        if self.expiration_date and today > self.expiration_date:
            return False
        
        return True
    
    @property
    def is_expired(self) -> bool:
        """Check if policy has expired"""
        if not self.expiration_date:
            return False
        
        today = datetime.utcnow().date()
        return today > self.expiration_date
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Days until policy expires"""
        if not self.expiration_date:
            return None
        
        today = datetime.utcnow().date()
        return (self.expiration_date - today).days
    
    @property
    def requires_review(self) -> bool:
        """Check if policy requires review"""
        if not self.next_review_date:
            return False
        
        today = datetime.utcnow().date()
        return today >= self.next_review_date
    
    async def publish(self, published_by_id: str):
        """Publish the policy"""
        self.status = PolicyStatus.ACTIVE
        self.published_by_id = published_by_id
        self.published_at = datetime.utcnow()
        
        # Set effective date if not set (default to tomorrow)
        if not self.effective_date:
            self.effective_date = datetime.utcnow().date() + timedelta(days=1)
        
        await self.save(update_fields=[
            "status", "published_by_id", "published_at", "effective_date"
        ])
    
    async def archive(self):
        """Archive the policy"""
        self.status = PolicyStatus.ARCHIVED
        self.archived_at = datetime.utcnow()
        await self.save(update_fields=["status", "archived_at"])
    
    async def create_new_version(self, new_content: str, changelog: str) -> 'PolicyDocument':
        """Create a new version of this policy"""
        new_policy = await PolicyDocument.create(
            policy_code=f"{self.policy_code.split('-')[0]}-{datetime.utcnow().year}-{self.version_number + 1}",
            title=self.title,
            short_title=self.short_title,
            policy_type=self.policy_type,
            version=f"{self.version_number + 1}.0",
            version_number=self.version_number + 1,
            content=new_content,
            summary=self.summary,
            changelog=changelog,
            audience=self.audience,
            regions=self.regions,
            languages=self.languages,
            previous_version=self,
            related_policies=self.related_policies,
            compliance_standards=self.compliance_standards,
            risk_level=self.risk_level,
            is_mandatory=self.is_mandatory,
            min_age_requirement=self.min_age_requirement,
            requires_explicit_consent=self.requires_explicit_consent,
            review_frequency=self.review_frequency
        )
        
        # Archive the old version
        await self.archive()
        
        return new_policy
    
    async def increment_view(self):
        """Increment view count"""
        self.view_count += 1
        await self.save(update_fields=["view_count"])
    
    async def increment_accept(self):
        """Increment accept count"""
        self.accept_count += 1
        await self.save(update_fields=["accept_count"])
    
    async def increment_decline(self):
        """Increment decline count"""
        self.decline_count += 1
        await self.save(update_fields=["decline_count"])
    
    async def set_next_review_date(self, months: int = 12):
        """Set next review date"""
        if not self.effective_date:
            self.effective_date = datetime.utcnow().date()
        
        self.next_review_date = self.effective_date + timedelta(days=months * 30)
        await self.save(update_fields=["next_review_date"])
    
    async def add_tag(self, tag: str):
        """Add a tag to the policy"""
        if tag not in self.tags:
            self.tags.append(tag)
            await self.save(update_fields=["tags"])
    
    async def add_compliance_standard(self, standard: str):
        """Add a compliance standard"""
        if standard not in self.compliance_standards:
            self.compliance_standards.append(standard)
            await self.save(update_fields=["compliance_standards"])
    
    @classmethod
    async def get_active_policy(
        cls,
        policy_type: PolicyType,
        audience: Optional[PolicyAudience] = None,
        region: Optional[str] = None
    ) -> Optional['PolicyDocument']:
        """Get the active policy for a given type"""
        today = datetime.utcnow().date()
        
        query = cls.filter(
            policy_type=policy_type,
            status=PolicyStatus.ACTIVE,
            effective_date__lte=today
        ).filter(
            fields.Q(expiration_date__isnull=True) | fields.Q(expiration_date__gte=today)
        )
        
        if audience:
            query = query.filter(audience=audience)
        
        if region:
            query = query.filter(regions__contains=[region])
        
        return await query.order_by("-version_number").first()
    
    @classmethod
    async def get_policies_requiring_review(cls) -> List['PolicyDocument']:
        """Get all policies that require review"""
        today = datetime.utcnow().date()
        
        return await cls.filter(
            status=PolicyStatus.ACTIVE,
            next_review_date__lte=today
        ).all()
    
    @classmethod
    async def get_user_required_policies(
        cls,
        user_country: str,
        user_age: int,
        user_type: str = "registered"
    ) -> List['PolicyDocument']:
        """Get all policies that a user must accept based on their profile"""
        today = datetime.utcnow().date()
        
        query = cls.filter(
            status=PolicyStatus.ACTIVE,
            effective_date__lte=today,
            is_mandatory=True
        ).filter(
            fields.Q(expiration_date__isnull=True) | fields.Q(expiration_date__gte=today)
        )
        
        # Filter by audience
        if user_type == "admin":
            audience_filter = fields.Q(audience=PolicyAudience.ADMINISTRATORS) | fields.Q(audience=PolicyAudience.ALL_USERS)
        elif user_type == "registered":
            audience_filter = fields.Q(audience=PolicyAudience.REGISTERED_USERS) | fields.Q(audience=PolicyAudience.ALL_USERS)
        else:
            audience_filter = fields.Q(audience=PolicyAudience.PUBLIC) | fields.Q(audience=PolicyAudience.ALL_USERS)
        
        query = query.filter(audience_filter)
        
        # Filter by region (global or user's region)
        query = query.filter(
            fields.Q(regions__contains=[PolicyRegion.GLOBAL]) | 
            fields.Q(regions__contains=[user_country])
        )
        
        # Filter by age requirement
        if user_age:
            query = query.filter(
                fields.Q(min_age_requirement__isnull=True) |
                fields.Q(min_age_requirement__lte=user_age)
            )
        
        return await query.order_by("policy_type", "-version_number").all()