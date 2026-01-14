from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator, RegexValidator, MaxLengthValidator
import uuid
from enum import IntEnum, Enum
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
import re
import secrets
import string

from .base_user import TimestampMixin,SoftDeleteMixin,AdminLevel

class AdminUser(Model, TimestampMixin, SoftDeleteMixin):
    user = fields.OneToOneField(
        "models.User",
        pk=True,
        related_name="admin_profile",
        on_delete=fields.CASCADE,
        index=True
    )
    
    admin_level = fields.IntEnumField(AdminLevel, default=AdminLevel.SUPPORT)
    employee_id = fields.CharField(
        max_length=50, 
        unique=True,
        validators=[RegexValidator(r'^EMP-[A-Z0-9]{6,}$',0)]
    )

    
    permissions = fields.JSONField(default={
        "user_management": {"view": False, "create": False, "edit": False, "delete": False, "ban": False, "verify": False},
        "property_management": {"view": False, "create": False, "edit": False, "delete": False, "approve": False, "feature": False},
        "content_management": {"manage_pages": False, "manage_blog": False, "manage_faq": False},
        "financial": {"view_transactions": False, "process_refunds": False, "manage_payouts": False},
        "reports": {"view": False, "export": False, "analytics": False},
        "system": {"manage_settings": False, "manage_api_keys": False, "view_logs": False}
    })
    
    department = fields.CharField(max_length=100, null=True)
    job_title = fields.CharField(max_length=100, null=True)
    
    is_active = fields.BooleanField(default=True)
    is_suspended = fields.BooleanField(default=False)
    suspension_reason = fields.TextField(null=True)
    suspension_until = fields.DatetimeField(null=True)
    
    admin_preferences = fields.JSONField(default={
        "dashboard_layout": "default",
        "email_notifications": True,
        "default_sort": "newest",
        "items_per_page": 50
    })
    
    last_login_ip = fields.CharField(max_length=45, null=True)
    last_activity = fields.DatetimeField(null=True)
    activity_log = fields.JSONField(default=list)
    
    session_timeout = fields.IntField(default=30)
    mfa_required = fields.BooleanField(default=True)
    
    supervisor = fields.ForeignKeyField(
        "models.AdminUser",
        related_name="subordinates",
        null=True,
        on_delete=fields.SET_NULL
    )
    assigned_teams = fields.JSONField(default=list)
    
    allowed_ips = fields.JSONField(default=list)
    allowed_countries = fields.JSONField(default=list)
    access_hours_start = fields.TimeField(null=True)
    access_hours_end = fields.TimeField(null=True)
    
    actions_taken = fields.IntField(default=0)
    tickets_resolved = fields.IntField(default=0)
    reports_generated = fields.IntField(default=0)
    
    class Meta:
        table = "admin_users"
        indexes = [
            ("employee_id",),
            ("department",),
            ("admin_level",),
            ("is_active",),
            # ("supervisor_id",),
            ("is_deleted", "is_active"),
        ]
        ordering = ["admin_level", "department"]
        
    async def save(self, *args, **kwargs):
        """Override save to auto-generate identifiers for Admin."""
        creating = self.pk is None
        
        if creating:
            # Auto-generate identifiers with Admin-specific prefixes
            if not self.public_id:
                self.public_id = await self.__class__.generate_unique_public_id("ADM")
            
            if not self.username:
                self.username = await self.__class__.generate_unique_username(
                    self.first_name, 
                    self.last_name
                )
            
            if not self.referral_code:
                self.referral_code = await self.__class__.generate_unique_referral_code("ADM")
        
        await super().save(*args, **kwargs)    
    
    async def validate_admin_requirements(self):
        errors = []
        
        if not self.user.email:
            errors.append("User must have an email address")
        
        if not self.user.phone_number and self.admin_level.value <= AdminLevel.ADMIN.value:
            errors.append("Admin users must have a phone number")
        
        if not re.match(r'^EMP-[A-Z0-9]{6,}$', self.employee_id):
            errors.append("Invalid employee ID format")
        
        if not self.user.is_active:
            errors.append("User account must be active to be an admin")
        
        if errors:
            raise ValueError("; ".join(errors))
    
    async def save(self, *args, **kwargs):
        if not re.match(r'^EMP-[A-Z0-9]{6,}$', self.employee_id):
            raise ValueError("Invalid employee ID format")
        await super().save(*args, **kwargs)

    async def has_permission(self, module: str, action: str) -> bool:
        module_perms = self.permissions.get(module, {})
        return module_perms.get(action, False)
    
    async def log_activity(self, action: str, details: Dict[str, Any]):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "ip_address": self.last_login_ip
        }
        
        self.activity_log = [log_entry] + self.activity_log[:99]
        self.last_activity = datetime.utcnow()
        self.actions_taken += 1
        
        await self.save(update_fields=["activity_log", "last_activity", "actions_taken"])
    
    async def suspend(self, reason: str, until: Optional[datetime] = None):
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspension_until = until
        await self.save(update_fields=["is_suspended", "suspension_reason", "suspension_until"])
    
    async def unsuspend(self):
        self.is_suspended = False
        self.suspension_reason = None
        self.suspension_until = None
        await self.save(update_fields=["is_suspended", "suspension_reason", "suspension_until"])
    
    @property
    def can_manage_users(self) -> bool:
        return self.has_permission("user_management", "view") or self.has_permission("user_management", "edit")
    
    @property
    def is_super_admin(self) -> bool:
        return self.admin_level == AdminLevel.SUPER_ADMIN