from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import IntEnum

from .index import PolicyType
    
class PolicyAcceptance(Model):
    """
    Tracks user acceptance of policies.
    Creates an audit trail of when users accepted which policies.
    """
    
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    user = fields.ForeignKeyField(
        'models.User',
        related_name='policy_acceptances',
        on_delete=fields.CASCADE,
        index=True
    )
    
    policy = fields.ForeignKeyField(
        'models.PolicyDocument',
        related_name='acceptances',
        on_delete=fields.CASCADE,
        index=True
    )
    
    accepted_version = fields.CharField(max_length=20)  # Version user accepted
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.TextField(null=True)
    
    # Method of acceptance
    accepted_via = fields.CharField(max_length=50, default="web")  # web, mobile, api, etc.
    
    # Consent details
    consent_type = fields.CharField(max_length=50, default="explicit")  # explicit, implicit, etc.
    consent_level = fields.CharField(max_length=50, default="full")  # full, limited, etc.
    
    # Withdrawal (if user later withdraws consent)
    withdrawn_at = fields.DatetimeField(null=True)
    withdrawal_reason = fields.TextField(null=True)
    withdrawal_ip = fields.CharField(max_length=45, null=True)
    
    # Timestamps
    accepted_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Metadata
    metadata = fields.JSONField(default=dict)
    
    class Meta:
        table = "policy_acceptances"
        indexes = [
            ("user_id", "policy_id"),
            ("user_id", "accepted_at"),
            ("policy_id", "accepted_at"),
            ("user_id", "withdrawn_at"),
        ]
        ordering = ["-accepted_at"]
        # Enforce one acceptance per user per policy version
        unique_together = (("user", "policy", "accepted_version"),)
    
    @property
    def is_active(self) -> bool:
        """Check if acceptance is still active (not withdrawn)"""
        return self.withdrawn_at is None
    
    @property
    def acceptance_age_days(self) -> int:
        """Days since acceptance"""
        return (datetime.utcnow() - self.accepted_at).days
    
    async def withdraw_consent(self, reason: str, ip_address: Optional[str] = None):
        """Withdraw consent for this policy"""
        self.withdrawn_at = datetime.utcnow()
        self.withdrawal_reason = reason
        
        if ip_address:
            self.withdrawal_ip = ip_address
        
        await self.save(update_fields=[
            "withdrawn_at", "withdrawal_reason", "withdrawal_ip"
        ])
    
    async def renew_acceptance(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Renew acceptance (create new acceptance for updated policy)"""
        # Create new acceptance record
        new_acceptance = await PolicyAcceptance.create(
            user_id=self.user_id,
            policy_id=self.policy_id,
            accepted_version=self.policy.version,
            ip_address=ip_address,
            user_agent=user_agent,
            accepted_via=self.accepted_via,
            consent_type=self.consent_type,
            consent_level=self.consent_level
        )
        
        return new_acceptance
    
    @classmethod
    async def has_accepted_policy(
        cls,
        user_id: str,
        policy_id: str,
        require_active: bool = True
    ) -> bool:
        """Check if user has accepted a specific policy"""
        query = cls.filter(
            user_id=user_id,
            policy_id=policy_id
        )
        
        if require_active:
            query = query.filter(withdrawn_at__isnull=True)
        
        return await query.exists()
    
    @classmethod
    async def get_user_acceptances(
        cls,
        user_id: str,
        policy_type: Optional[PolicyType] = None,
        only_active: bool = True
    ) -> List['PolicyAcceptance']:
        """Get all policy acceptances for a user"""
        query = cls.filter(user_id=user_id).prefetch_related('policy')
        
        if only_active:
            query = query.filter(withdrawn_at__isnull=True)
        
        if policy_type:
            query = query.filter(policy__policy_type=policy_type)
        
        return await query.order_by("-accepted_at").all()
    
    @classmethod
    async def get_policy_acceptance_stats(cls, policy_id: str) -> Dict[str, Any]:
        """Get acceptance statistics for a policy"""
        total = await cls.filter(policy_id=policy_id).count()
        active = await cls.filter(policy_id=policy_id, withdrawn_at__isnull=True).count()
        withdrawn = total - active
        
        return {
            "total_acceptances": total,
            "active_acceptances": active,
            "withdrawn_acceptances": withdrawn,
            "withdrawal_rate": (withdrawn / total * 100) if total > 0 else 0
        }