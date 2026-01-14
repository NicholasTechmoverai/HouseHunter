from tortoise.models import Model
from tortoise import fields
import uuid
from typing import Optional, Dict, Any, List
from enum import IntEnum
from datetime import datetime


class ShareMethod(IntEnum):
    """Methods of sharing"""
    LINK = 1
    EMAIL = 2
    SMS = 3
    WHATSAPP = 4
    TELEGRAM = 5
    FACEBOOK = 6
    TWITTER = 7
    LINKEDIN = 8
    INSTAGRAM = 9
    COPY_LINK = 10
    QR_CODE = 11


class ShareStatus(IntEnum):
    """Status of shared item"""
    PENDING = 1  # Share created but not sent
    SENT = 2     # Share sent to recipient
    VIEWED = 3   # Recipient viewed the shared item
    CLICKED = 4  # Recipient clicked/interacted
    EXPIRED = 5
    REVOKED = 6  # Share revoked by sender
    FAILED = 7   # Failed to send


class SharePermission(IntEnum):
    """Permissions for shared content"""
    VIEW_ONLY = 1
    COMMENT = 2
    EDIT = 3
    SHARE = 4
    ADMIN = 5


class BaseShare(Model):
    """
    Abstract base model for sharing/forwarding functionality.
    Tracks shares of properties, listings, documents, etc.
    """
    
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    # Share identifier for URL
    share_code = fields.CharField(max_length=50, unique=True, index=True)
    
    # Sender (who is sharing)
    sender = fields.ForeignKeyField(
        'models.User',
        related_name='sent_shares',
        on_delete=fields.CASCADE,
        index=True
    )
    
    # Recipient (who receives the share)
    recipient = fields.ForeignKeyField(
        'models.User',
        related_name='received_shares',
        null=True,
        on_delete=fields.SET_NULL,
        index=True
    )
    
    # Recipient info (if not a registered user)
    recipient_email = fields.CharField(max_length=255, null=True, index=True)
    recipient_phone = fields.CharField(max_length=20, null=True, index=True)
    recipient_name = fields.CharField(max_length=200, null=True)
    
    # Item being shared
    item_type = fields.CharField(max_length=50, index=True)  # e.g., "property", "document"
    item_id = fields.CharField(max_length=100, index=True)
    
    # Share details
    share_method = fields.IntEnumField(ShareMethod, index=True)
    share_url = fields.TextField()  # Generated share URL
    
    # Message/note from sender
    message = fields.TextField(null=True)
    
    # Permissions
    permission_level = fields.IntEnumField(SharePermission, default=SharePermission.VIEW_ONLY)
    expires_at = fields.DatetimeField(null=True, index=True)
    password = fields.CharField(max_length=255, null=True)  # Optional password protection
    
    # Status tracking
    status = fields.IntEnumField(ShareStatus, default=ShareStatus.PENDING, index=True)
    
    # Delivery tracking
    sent_at = fields.DatetimeField(null=True)
    viewed_at = fields.DatetimeField(null=True)
    clicked_at = fields.DatetimeField(null=True)
    
    # Analytics
    view_count = fields.IntField(default=0)
    click_count = fields.IntField(default=0)
    last_accessed_at = fields.DatetimeField(null=True)
    
    # Metadata
    metadata = fields.JSONField(default=dict)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Revocation
    revoked_at = fields.DatetimeField(null=True)
    revoked_reason = fields.TextField(null=True)
    
    class Meta:
        abstract = True
        indexes = [
            ("share_code",),
            ("sender_id", "created_at"),
            ("recipient_id", "status"),
            ("recipient_email", "status"),
            ("item_type", "item_id", "status"),
            ("expires_at", "status"),
        ]
        ordering = ["-created_at"]
    
    @property
    def is_expired(self) -> bool:
        """Check if share has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Check if share is active"""
        return (
            self.status in [ShareStatus.SENT, ShareStatus.VIEWED, ShareStatus.CLICKED] 
            and not self.is_expired
            and not self.revoked_at
        )
    
    @property
    def recipient_identifier(self) -> str:
        """Get recipient identifier (email, phone, or user ID)"""
        if self.recipient:
            return str(self.recipient.id)
        elif self.recipient_email:
            return f"email:{self.recipient_email}"
        elif self.recipient_phone:
            return f"phone:{self.recipient_phone}"
        return "anonymous"
    
    async def mark_as_sent(self):
        """Mark share as sent"""
        self.status = ShareStatus.SENT
        self.sent_at = datetime.utcnow()
        await self.save(update_fields=["status", "sent_at"])
    
    async def mark_as_viewed(self):
        """Mark share as viewed by recipient"""
        self.status = ShareStatus.VIEWED
        self.viewed_at = datetime.utcnow()
        self.view_count += 1
        self.last_accessed_at = datetime.utcnow()
        await self.save(update_fields=[
            "status", "viewed_at", "view_count", "last_accessed_at"
        ])
    
    async def mark_as_clicked(self):
        """Mark share as clicked by recipient"""
        self.status = ShareStatus.CLICKED
        self.clicked_at = datetime.utcnow()
        self.click_count += 1
        self.last_accessed_at = datetime.utcnow()
        await self.save(update_fields=[
            "status", "clicked_at", "click_count", "last_accessed_at"
        ])
    
    async def revoke(self, reason: Optional[str] = None):
        """Revoke the share"""
        self.status = ShareStatus.REVOKED
        self.revoked_at = datetime.utcnow()
        self.revoked_reason = reason
        await self.save(update_fields=[
            "status", "revoked_at", "revoked_reason"
        ])
    
    async def expire(self):
        """Manually expire the share"""
        self.status = ShareStatus.EXPIRED
        await self.save(update_fields=["status"])
    
    async def generate_share_code(self) -> str:
        """Generate unique share code"""
        import secrets
        import string
        
        if not self.share_code:
            alphabet = string.ascii_letters + string.digits
            code = ''.join(secrets.choice(alphabet) for _ in range(12))
            
            # Ensure uniqueness
            while await self.__class__.filter(share_code=code).exists():
                code = ''.join(secrets.choice(alphabet) for _ in range(12))
            
            self.share_code = code
            await self.save(update_fields=["share_code"])
        
        return self.share_code
    
    @classmethod
    async def create_share(
        cls,
        sender_id: str,
        item_type: str,
        item_id: str,
        recipient_info: Dict[str, Any],
        permission: SharePermission = SharePermission.VIEW_ONLY,
        expires_hours: Optional[int] = None,
        message: Optional[str] = None
    ) -> 'BaseShare':
        """Create a new share with proper setup"""
        share = await cls.create(
            sender_id=sender_id,
            item_type=item_type,
            item_id=item_id,
            recipient_email=recipient_info.get('email'),
            recipient_phone=recipient_info.get('phone'),
            recipient_name=recipient_info.get('name'),
            permission_level=permission,
            message=message,
            expires_at=(
                datetime.utcnow() + timedelta(hours=expires_hours)
                if expires_hours else None
            ),
            metadata={
                "user_agent": recipient_info.get('user_agent'),
                "ip_address": recipient_info.get('ip_address'),
                "platform": recipient_info.get('platform'),
            }
        )
        
        # Generate share code and URL
        await share.generate_share_code()
        share.share_url = f"/share/{share.share_code}"
        await share.save(update_fields=["share_url"])
        
        return share