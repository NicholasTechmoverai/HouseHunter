from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import json
from enum import IntEnum

from ..defaults.index import TimestampMixin


class NotificationType(IntEnum):
    SYSTEM = 1
    USER = 2
    PROPERTY = 3
    TRANSACTION = 4
    SECURITY = 5
    MARKETING = 6
    SOCIAL = 7
    SUPPORT = 8
    ALERT = 9
    REMINDER = 10


class NotificationPriority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class NotificationStatus(IntEnum):
    PENDING = 1
    SENT = 2
    DELIVERED = 3
    READ = 4
    CLICKED = 5
    FAILED = 6
    ARCHIVED = 7
    EXPIRED = 8


class NotificationChannel(IntEnum):
    EMAIL = 1
    SMS = 2
    PUSH = 3
    IN_APP = 4
    WEB_PUSH = 5
    WHATSAPP = 6
    TELEGRAM = 7


class NotificationCategory(IntEnum):
    ACCOUNT = 1
    SECURITY = 2
    PROPERTY = 3
    PAYMENT = 4
    BOOKING = 5
    MESSAGE = 6
    REVIEW = 7
    PROMOTION = 8
    SYSTEM = 9
    SOCIAL = 10


class UserNotification(Model, TimestampMixin):
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    notification_id = fields.CharField(max_length=50, unique=True, index=True)
    
    user = fields.ForeignKeyField(
        'models.User',
        related_name='notifications',
        null=True,
        on_delete=fields.CASCADE,
        index=True
    )
    
    notification_type = fields.IntEnumField(
        NotificationType, 
        default=NotificationType.SYSTEM,
        index=True
    )
    
    category = fields.IntEnumField(
        NotificationCategory,
        default=NotificationCategory.SYSTEM,
        index=True
    )
    
    priority = fields.IntEnumField(
        NotificationPriority,
        default=NotificationPriority.NORMAL,
        index=True
    )
    
    status = fields.IntEnumField(
        NotificationStatus,
        default=NotificationStatus.PENDING,
        index=True
    )
    
    channels = fields.JSONField(default=list)
    
    title = fields.CharField(max_length=200)
    message = fields.TextField()
    
    short_message = fields.CharField(max_length=160, null=True)
    
    data = fields.JSONField(default=dict)
    
    action_url = fields.TextField(null=True)
    action_label = fields.CharField(max_length=50, null=True)
    
    deep_link = fields.TextField(null=True)
    web_url = fields.TextField(null=True)
    
    icon = fields.CharField(max_length=100, null=True)
    image_url = fields.TextField(null=True)
    
    sender_id = fields.ForeignKeyField(
        'models.User',
        related_name='sent_notifications',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    sender_type = fields.CharField(max_length=50, null=True)
    
    related_entity_type = fields.CharField(max_length=50, null=True)
    related_entity_id = fields.CharField(max_length=100, null=True)
    
    group_key = fields.CharField(max_length=100, null=True, index=True)
    
    read_at = fields.DatetimeField(null=True)
    delivered_at = fields.DatetimeField(null=True)
    clicked_at = fields.DatetimeField(null=True)
    acknowledged_at = fields.DatetimeField(null=True)
    
    expires_at = fields.DatetimeField(null=True)
    scheduled_for = fields.DatetimeField(null=True, index=True)
    sent_at = fields.DatetimeField(null=True)
    
    delivery_attempts = fields.IntField(default=0)
    max_attempts = fields.IntField(default=3)
    
    delivery_errors = fields.JSONField(default=list)
    
    device_tokens = fields.JSONField(default=list)
    email_addresses = fields.JSONField(default=list)
    phone_numbers = fields.JSONField(default=list)
    
    template_id = fields.CharField(max_length=100, null=True)
    template_variables = fields.JSONField(default=dict)
    
    locale = fields.CharField(max_length=10, default='en')
    
    metadata = fields.JSONField(default=dict)
    
    tags = fields.JSONField(default=list)
    
    silent = fields.BooleanField(default=False)
    badge_count = fields.IntField(default=1)
    
    campaign_id = fields.CharField(max_length=100, null=True, index=True)
    batch_id = fields.CharField(max_length=100, null=True, index=True)
    
    read_receipt_requested = fields.BooleanField(default=False)
    requires_acknowledgment = fields.BooleanField(default=False)
    
    cost = fields.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    user_preferences_override = fields.JSONField(default=dict)
    
    is_test = fields.BooleanField(default=False)
    is_bulk = fields.BooleanField(default=False)
    
    analytics_data = fields.JSONField(default=dict)
    
    class Meta:
        table = "user_notifications"
        indexes = [
            ("user_id", "status"),
            ("user_id", "read_at"),
            ("user_id", "created_at"),
            ("notification_id",),
            ("group_key",),
            ("scheduled_for", "status"),
            ("priority", "status"),
            ("category", "status"),
            ("campaign_id",),
            ("batch_id",),
            ("expires_at", "status"),
            ("user_id", "notification_type", "status"),
            ("related_entity_type", "related_entity_id"),
        ]
        ordering = ["-created_at"]

    @property
    def is_read(self) -> bool:
        return self.status == NotificationStatus.READ or self.read_at is not None

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_scheduled(self) -> bool:
        return self.scheduled_for is not None

    @property
    def can_send(self) -> bool:
        if self.is_expired:
            return False
        
        if self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ]:
            return False
        
        if self.is_scheduled:
            return datetime.utcnow() >= self.scheduled_for
        
        return True

    @property
    def age_in_hours(self) -> float:
        delta = datetime.utcnow() - self.created_at
        return delta.total_seconds() / 3600

    async def mark_as_read(self):
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
        
        await self.save(update_fields=["status", "read_at"])

    async def mark_as_delivered(self, channel: Optional[str] = None):
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
        
        if channel and channel not in self.channels:
            self.channels.append(channel)
        
        await self.save(update_fields=["status", "delivered_at", "channels"])

    async def mark_as_sent(self, channel: Optional[str] = None):
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()
        
        if channel and channel not in self.channels:
            self.channels.append(channel)
        
        await self.save(update_fields=["status", "sent_at", "channels"])

    async def mark_as_clicked(self):
        self.status = NotificationStatus.CLICKED
        self.clicked_at = datetime.utcnow()
        
        await self.save(update_fields=["status", "clicked_at"])

    async def mark_as_failed(self, error_message: str):
        self.status = NotificationStatus.FAILED
        
        if not self.delivery_errors:
            self.delivery_errors = []
        
        self.delivery_errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "attempt": self.delivery_attempts,
            "error": error_message
        })
        
        self.delivery_attempts += 1
        
        await self.save(update_fields=[
            "status", 
            "delivery_errors", 
            "delivery_attempts"
        ])

    async def archive(self):
        self.status = NotificationStatus.ARCHIVED
        await self.save(update_fields=["status"])

    async def schedule(self, send_at: datetime):
        self.scheduled_for = send_at
        self.status = NotificationStatus.PENDING
        
        await self.save(update_fields=["scheduled_for", "status"])

    async def add_channel(self, channel: str):
        if not self.channels:
            self.channels = []
        
        if channel not in self.channels:
            self.channels.append(channel)
        
        await self.save(update_fields=["channels"])

    async def add_device_token(self, token: str, platform: str):
        if not self.device_tokens:
            self.device_tokens = []
        
        token_data = {
            "token": token,
            "platform": platform,
            "added_at": datetime.utcnow().isoformat()
        }
        
        self.device_tokens.append(token_data)
        await self.save(update_fields=["device_tokens"])

    async def add_delivery_error(self, error: str, channel: str):
        if not self.delivery_errors:
            self.delivery_errors = []
        
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
            "error": error
        }
        
        self.delivery_errors.append(error_data)
        await self.save(update_fields=["delivery_errors"])

    async def update_analytics(self, event: str, data: Dict[str, Any]):
        if not self.analytics_data:
            self.analytics_data = {}
        
        if event not in self.analytics_data:
            self.analytics_data[event] = []
        
        self.analytics_data[event].append({
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
        
        await self.save(update_fields=["analytics_data"])

    async def resend(self, new_channels: Optional[List[str]] = None):
        if new_channels:
            self.channels = new_channels
        
        self.status = NotificationStatus.PENDING
        self.delivery_attempts = 0
        
        await self.save(update_fields=["status", "channels", "delivery_attempts"])

    async def add_tag(self, tag: str):
        if not self.tags:
            self.tags = []
        
        if tag not in self.tags:
            self.tags.append(tag)
        
        await self.save(update_fields=["tags"])

    async def set_expiration(self, hours: int = 24):
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        await self.save(update_fields=["expires_at"])

    @property
    def delivery_summary(self) -> Dict[str, Any]:
        return {
            "attempts": self.delivery_attempts,
            "channels": self.channels,
            "status": self.status.name,
            "last_error": self.delivery_errors[-1] if self.delivery_errors else None,
            "sent_at": self.sent_at,
            "delivered_at": self.delivered_at,
            "read_at": self.read_at
        }

    @property
    def is_urgent(self) -> bool:
        return self.priority in [NotificationPriority.URGENT, NotificationPriority.CRITICAL]

    async def acknowledge(self):
        self.acknowledged_at = datetime.utcnow()
        await self.save(update_fields=["acknowledged_at"])

    @classmethod
    async def create_bulk_notification(
        cls,
        users: List['User'],
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        **kwargs
    ) -> List['UserNotification']:
        notifications = []
        batch_id = f"BATCH-{uuid.uuid4().hex[:16]}"
        
        for user in users:
            notification = await cls.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                category=category,
                batch_id=batch_id,
                is_bulk=True,
                **kwargs
            )
            notifications.append(notification)
        
        return notifications

    async def duplicate_for_user(self, new_user: 'User') -> 'UserNotification':
        new_notification = await UserNotification.create(
            user=new_user,
            title=self.title,
            message=self.message,
            notification_type=self.notification_type,
            category=self.category,
            priority=self.priority,
            channels=self.channels.copy() if self.channels else [],
            data=self.data.copy() if self.data else {},
            action_url=self.action_url,
            action_label=self.action_label,
            template_id=self.template_id,
            template_variables=self.template_variables.copy() if self.template_variables else {}
        )
        
        return new_notification

    @property
    def is_actionable(self) -> bool:
        return bool(self.action_url) or bool(self.deep_link)