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
import hashlib
import hmac

from models.defaults.index import TimestampMixin, SoftDeleteMixin

defaultAvatar = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"

class UserStatus(IntEnum):
    UNVERIFIED = 0
    ACTIVE = 1
    SUSPENDED = 2
    DEACTIVATED = 3
    DELETED = 4
    BANNED = 5

class AccountType(IntEnum):
    PERSONAL = 1
    BUSINESS = 2
    AGENT = 3
    ADMIN = 4

class Gender(IntEnum):
    MALE = 1
    FEMALE = 2
    NON_BINARY = 3
    PREFER_NOT_TO_SAY = 4
    OTHER = 5

class AdminLevel(IntEnum):
    SUPER_ADMIN = 1
    ADMIN = 2
    MODERATOR = 3
    SUPPORT = 4
    ANALYST = 5

class LoginProvider(Enum):
    GOOGLE = "google"
    APPLE = "apple"
    FACEBOOK = "facebook"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    LOCAL = "local"

class AuditMixin:
    last_password_changed = fields.DatetimeField(null=True)
    password_changed_count = fields.IntField(default=0)
    email_changed_at = fields.DatetimeField(null=True)
    phone_changed_at = fields.DatetimeField(null=True)

class BaseUser(Model, TimestampMixin, SoftDeleteMixin, AuditMixin):
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    public_id = fields.CharField(
        max_length=12,
        unique=True,
        null=True,
        validator=RegexValidator(r'^[A-Z]{3}-[A-Z0-9]{8}$',0) 
    )
    
    oauth_providers = fields.JSONField(default=dict)
    
    email = fields.CharField(
        max_length=255, 
        unique=True,
        validators=[
            RegexValidator(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 0),
            MaxLengthValidator(255)
        ]
    )
    password_hash = fields.CharField(max_length=255, null=True)
    password_salt = fields.CharField(max_length=255, null=True)
    
    mfa_enabled = fields.BooleanField(default=False)
    mfa_secret = fields.CharField(max_length=255, null=True)
    mfa_backup_codes = fields.JSONField(null=True)
    failed_login_attempts = fields.IntField(default=0)
    locked_until = fields.DatetimeField(null=True)
    
    username = fields.CharField(
        max_length=30, 
        unique=True,
        null=True,
        validators=[
            MinLengthValidator(3),
            MaxLengthValidator(30),
            RegexValidator(r'^[a-zA-Z0-9_]+$', 0)
        ]
    )
    display_name = fields.CharField(max_length=100, null=True)
    
    first_name = fields.CharField(max_length=50, validators=[MaxLengthValidator(50)])
    last_name = fields.CharField(max_length=50, validators=[MaxLengthValidator(50)])
    middle_name = fields.CharField(max_length=50, null=True)
    
    date_of_birth = fields.DateField(null=True)
    gender = fields.IntEnumField(Gender, null=True)
    
    email_verified = fields.BooleanField(default=False)
    email_verified_at = fields.DatetimeField(null=True)
    
    phone_number = fields.CharField(
        max_length=20, 
        null=True, 
        unique=True,
        validators=[RegexValidator(r'^\+?[1-9]\d{1,14}$',0)]
    )
    phone_country_code = fields.CharField(max_length=5, default='+254')
    phone_verified = fields.BooleanField(default=False)
    phone_verified_at = fields.DatetimeField(null=True)
    
    secondary_email = fields.CharField(max_length=255, null=True)
    secondary_phone = fields.CharField(max_length=20, null=True)
    
    country = fields.CharField(max_length=2, default='KE')
    timezone = fields.CharField(max_length=50, default='Africa/Nairobi')
    locale = fields.CharField(max_length=10, default='en-KE')
    currency = fields.CharField(max_length=3, default='KES')
    
    account_type = fields.IntEnumField(AccountType, default=AccountType.PERSONAL)
    account_type_set_at = fields.DatetimeField(null=True)

    status = fields.IntEnumField(UserStatus, default=UserStatus.UNVERIFIED)
    activated_status_at = fields.DatetimeField(null=True)
    
    last_login = fields.DatetimeField(null=True)
    last_login_ip = fields.CharField(max_length=45, null=True)
    last_active = fields.DatetimeField(null=True)
    
    preferences = fields.JSONField(default=dict)
    
    consent_given = fields.BooleanField(default=False)
    consent_given_at = fields.DatetimeField(null=True)
    gdpr_consents = fields.JSONField(null=True)
    data_processing_consent = fields.BooleanField(default=False)
    
    signup_source = fields.CharField(max_length=50, null=True)
    signup_ip = fields.CharField(max_length=45, null=True)
    signup_user_agent = fields.TextField(null=True)
    
    utm_source = fields.CharField(max_length=100, null=True)
    utm_medium = fields.CharField(max_length=100, null=True)
    referral_code = fields.CharField(max_length=20, null=True, unique=True)
    referred_by = fields.ForeignKeyField(
        'models.User', 
        related_name='referrals',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    profile_picture = fields.TextField(default=defaultAvatar)
    profile_picture_thumbnail = fields.TextField(default=defaultAvatar)
    profile_banner = fields.TextField(null=True)
    
    verification_level = fields.IntField(default=0)
    id_verified = fields.BooleanField(default=False)
    id_verified_at = fields.DatetimeField(null=True)
    id_document_type = fields.CharField(max_length=50, null=True)
    id_document_number = fields.CharField(max_length=50, null=True)
    
    account_tier = fields.CharField(max_length=20, default='basic')
    daily_rate_limit = fields.IntField(default=100)
    monthly_request_limit = fields.IntField(default=1000)
    
    class Meta:
        abstract = True
        indexes = [
            ("username",),
            ("email",),
            ("phone_number",),
            ("status",),
            ("created_at",),
            ("last_active",),
            ("country",),
            ("account_type",),
            ("referral_code",),
            ("referred_by_id",),
            ("is_deleted", "status"),
        ]
        ordering = ["-created_at"]
    
    @staticmethod
    def generate_salt():
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password, salt):
        salted_password = f"{password}{salt}"
        hash_obj = hashlib.sha256()
        hash_obj.update(salted_password.encode('utf-8'))
        hash_value = hash_obj.hexdigest()
        
        for _ in range(10000):
            hash_obj = hashlib.sha256()
            hash_obj.update(f"{hash_value}{salt}".encode('utf-8'))
            hash_value = hash_obj.hexdigest()
        
        return f"sha256:10000:{salt}:{hash_value}"
    
    @staticmethod
    def verify_password(password, password_hash):
        if not password_hash or not password:
            return False
        
        try:
            parts = password_hash.split(':')
            if len(parts) != 4:
                return False
            
            algorithm, iterations_str, salt, stored_hash = parts
            if algorithm != 'sha256':
                return False
            
            iterations = int(iterations_str)
            salted_password = f"{password}{salt}"
            hash_obj = hashlib.sha256()
            hash_obj.update(salted_password.encode('utf-8'))
            hash_value = hash_obj.hexdigest()
            
            for _ in range(iterations):
                hash_obj = hashlib.sha256()
                hash_obj.update(f"{hash_value}{salt}".encode('utf-8'))
                hash_value = hash_obj.hexdigest()
            
            return hmac.compare_digest(hash_value, stored_hash)
        except (ValueError, IndexError):
            return False
    
    def set_password(self, password):
        salt = self.generate_salt()
        self.password_salt = salt
        self.password_hash = self.hash_password(password, salt)
        self.last_password_changed = datetime.utcnow()
        self.password_changed_count += 1
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def check_password(self, password):
        return self.verify_password(password, self.password_hash)
    
    @property
    def full_name(self):
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.last_name)
        return " ".join(filter(None, names))
    
    @property
    def is_active(self):
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_authenticated(self):
        return self.is_active and (self.email_verified or self.phone_verified)  and not self.is_deleted
    
    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def is_adult(self):
        return self.age is not None and self.age >= 18
    
    async def update_last_login(self, ip_address=None):
        self.last_login = datetime.utcnow()
        self.last_login_ip = ip_address
        await self.save(update_fields=["last_login", "last_login_ip"])
    
    async def update_last_active(self):
        self.last_active = datetime.utcnow()
        await self.save(update_fields=["last_active"])
    
    async def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
        await self.save(update_fields=["failed_login_attempts", "locked_until"])
    
    async def reset_failed_logins(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        await self.save(update_fields=["failed_login_attempts", "locked_until"])
    
    async def verify_email(self):
        self.email_verified = True
        self.email_verified_at = datetime.utcnow()
        if self.status == UserStatus.UNVERIFIED:
            self.status = UserStatus.ACTIVE
        await self.save(update_fields=["email_verified", "email_verified_at", "status"])
    
    async def verify_phone(self):
        self.phone_verified = True
        self.phone_verified_at = datetime.utcnow()
        await self.save(update_fields=["phone_verified", "phone_verified_at"])
        
        
    async def activate_account(self):
        self.status = UserStatus.ACTIVE
        self.activated_status_at = datetime.utcnow()
        await self.save()
    
    async def deactivate_account(self, reason=""):
        self.status = UserStatus.DEACTIVATED
        self.deactivated_at = datetime.utcnow()
        self.deactivation_reason = reason
        await self.save()
    
    @classmethod
    async def generate_unique_public_id(cls, prefix="USR"):
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = f"{prefix}-{''.join(secrets.choice(alphabet) for _ in range(8))}"
            if not await cls.filter(public_id=code).exists():
                return code
    
    @classmethod
    async def generate_unique_username(cls, first_name="", last_name=""):
        if first_name and last_name:
            base = f"{first_name.lower()}.{last_name.lower()}"
        elif first_name:
            base = first_name.lower()
        elif last_name:
            base = last_name.lower()
        else:
            base = "user"
        
        base = re.sub(r'[^a-z0-9_]', '', base)
        
        if len(base) < 3:
            base = f"{base}{secrets.token_hex(2)}"
        
        if not await cls.filter(username=base).exists():
            return base[:30]
        
        counter = 1
        while counter < 1000:
            username = f"{base}{counter}"
            if len(username) > 30:
                username = f"{base[:27]}{counter}"
            
            if not await cls.filter(username=username).exists():
                return username
            counter += 1
        
        return f"user{secrets.token_hex(8)}"[:30]
    
    @classmethod
    async def generate_unique_referral_code(cls, prefix="REF"):
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = f"{prefix}{''.join(secrets.choice(alphabet) for _ in range(8))}"
            if not await cls.filter(referral_code=code).exists():
                return code
    
    async def ensure_public_id(self, prefix="USR"):
        if not self.public_id:
            self.public_id = await self.__class__.generate_unique_public_id(prefix)
            await self.save(update_fields=["public_id"])
        return self.public_id
    
    async def ensure_username(self):
        if not self.username:
            self.username = await self.__class__.generate_unique_username(
                self.first_name, 
                self.last_name
            )
            await self.save(update_fields=["username"])
        return self.username
    
    async def ensure_referral_code(self, prefix="REF"):
        if not self.referral_code:
            self.referral_code = await self.__class__.generate_unique_referral_code(prefix)
            await self.save(update_fields=["referral_code"])
        return self.referral_code
    
    async def ensure_all_identifiers(self, public_id_prefix="USR", referral_prefix="REF"):
        public_id = await self.ensure_public_id(public_id_prefix)
        username = await self.ensure_username()
        referral_code = await self.ensure_referral_code(referral_prefix)
        
        return {
            "public_id": public_id,
            "username": username,
            "referral_code": referral_code
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for API responses."""
        return {
            "public_id": self.public_id,
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "profile_picture": self.profile_picture,
            "profile_picture_thumbnail": self.profile_picture_thumbnail,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "country": self.country,
            "status": self.status.name if self.status else None,
            "account_type": self.account_type.name if self.account_type else None,
            "is_email_verified": self.email_verified,
            "is_phone_verified": self.phone_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }    