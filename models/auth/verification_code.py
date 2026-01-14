from tortoise import fields
from tortoise.models import Model
from uuid import uuid4
from enum import Enum
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

class VerificationType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR_AUTH = "two_factor_auth"
    ACCOUNT_RECOVERY = "account_recovery"
    EMAIL_CHANGE = "email_change"

class VerificationCodesStatus(str, Enum):
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"

class VerificationCodes(Model):
    id = fields.CharField(pk=True, max_length=36)
    
    user = fields.ForeignKeyField(
        "models.User",
        related_name="verification_codes",
        on_delete=fields.CASCADE
    )
    
    code = fields.CharField(max_length=10, index=True)
    type = fields.CharEnumField(VerificationType, index=True)
    identifier = fields.CharField(max_length=255, null=True)

    is_used = fields.BooleanField(default=False, index=True)
    used_at = fields.DatetimeField(null=True)

    expires_at = fields.DatetimeField(null=True)
    status = fields.CharEnumField(VerificationCodesStatus, default=VerificationCodesStatus.PENDING, index=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "verification_codes"
        indexes = [
            ("type", "status", "expires_at"),
            ("user_id", "type", "status"),
            ("code", "type", "status"),
        ]
        ordering = ["-created_at"]

    async def save(self, *args, **kwargs):
        creating = not self._saved_in_db
        if creating:
            if not self.id:
                self.id = str(uuid4())
            if not self.expires_at:
                self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        await super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.type}: {self.code}"
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    
    def is_valid(self) -> bool:
        return self.status == VerificationCodesStatus.PENDING and not self.is_used and not self.is_expired()
    
    async def mark_as_used(self):
        self.is_used = True
        self.status = VerificationCodesStatus.USED
        self.used_at = datetime.now(timezone.utc)
        await self.save()
    
    async def mark_as_expired(self):
        self.status = VerificationCodesStatus.EXPIRED
        await self.save()
    
    @staticmethod
    def generate_salt():
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_code(code: str, salt: str) -> str:
        salted_code = f"{code}{salt}"
        hash_obj = hashlib.sha256()
        hash_obj.update(salted_code.encode('utf-8'))
        hash_value = hash_obj.hexdigest()
        
        for _ in range(10000):
            hash_obj = hashlib.sha256()
            hash_obj.update(f"{hash_value}{salt}".encode('utf-8'))
            hash_value = hash_obj.hexdigest()
        
        return f"sha256:10000:{salt}:{hash_value}"
    
    @staticmethod
    def verify_code(code: str, code_hash: str) -> bool:
        if not code_hash or not code:
            return False
        
        try:
            parts = code_hash.split(':')
            if len(parts) != 4:
                return False
            
            algorithm, iterations_str, salt, stored_hash = parts
            if algorithm != 'sha256':
                return False
            
            iterations = int(iterations_str)
            salted_code = f"{code}{salt}"
            hash_obj = hashlib.sha256()
            hash_obj.update(salted_code.encode('utf-8'))
            hash_value = hash_obj.hexdigest()
            
            for _ in range(iterations):
                hash_obj = hashlib.sha256()
                hash_obj.update(f"{hash_value}{salt}".encode('utf-8'))
                hash_value = hash_obj.hexdigest()
            
            return hmac.compare_digest(hash_value, stored_hash)
        except (ValueError, IndexError):
            return False
    
    def to_dict(self) -> dict:
        now = datetime.now(timezone.utc)

        return {
            "id": self.id,
            "code": self.code,
            "type": self.type,
            "identifier": self.identifier,
            "is_used": self.is_used,
            "status": self.status,
            "is_valid": self.is_valid(),
            "is_expired": self.is_expired(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_in": (self.expires_at - now).total_seconds() if self.expires_at else 0,
        }
