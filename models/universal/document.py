from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator, RegexValidator
import uuid
from enum import IntEnum
from datetime import datetime
import os
from pathlib import Path
import mimetypes
from typing import Optional, Dict, Any, Tuple, BinaryIO
import hashlib
from models.defaults.index import TimestampMixin, SoftDeleteMixin
from datetime import datetime, timedelta


related_fields = {
    "user": "models.User",
    "admin": "models.AdminUser",
    "uploaded_documents":""
}


class VerificationStatus(IntEnum):
    PENDING = 0
    VERIFIED = 1
    REJECTED = 2
    EXPIRED = 3
    SUSPENDED = 4
    UNDER_REVIEW = 5


class DocumentType(IntEnum):
    NATIONAL_ID = 1
    PASSPORT = 2
    DRIVERS_LICENSE = 3
    BUSINESS_LICENSE = 4
    TAX_CERTIFICATE = 5
    UTILITY_BILL = 6
    BANK_STATEMENT = 7
    CONTRACT = 8
    CERTIFICATE = 9
    OTHER = 10


class DocumentStatus(IntEnum):
    UPLOADED = 1
    PROCESSING = 2
    PROCESSED = 3
    FAILED = 4
    DELETED = 5


class IdentityDocument(Model, TimestampMixin, SoftDeleteMixin):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    
    document_type = fields.IntEnumField(DocumentType, index=True)
    document_number = fields.CharField(max_length=100, index=True, null=True)
    
    original_filename = fields.CharField(max_length=255)
    file_path = fields.TextField()
    file_url = fields.TextField()
    
    file_size = fields.BigIntField(default=0)
    mime_type = fields.CharField(max_length=100, null=True)
    file_hash = fields.CharField(max_length=64, null=True, index=True)
    
    pages = fields.IntField(default=1)
    width = fields.IntField(null=True)
    height = fields.IntField(null=True)
    
    uploaded_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField(null=True, index=True)
    
    verification_status = fields.IntEnumField(
        VerificationStatus, 
        default=VerificationStatus.PENDING,
        index=True
    )
    document_status = fields.IntEnumField(
        DocumentStatus,
        default=DocumentStatus.UPLOADED,
        index=True
    )
    
    verification_notes = fields.TextField(null=True)
    rejection_reason = fields.TextField(null=True)
    
    metadata = fields.JSONField(default=dict)
    
    uploaded_by = fields.ForeignKeyField(
        related_fields['user'],
        related_name='uploaded_documents',
        null=True,
        on_delete=fields.SET_NULL
    )
    
    verified_by = fields.ForeignKeyField(
        related_fields['admin'],
        null=True,
        related_name='verified_documents',
        on_delete=fields.SET_NULL
    )
    
    verified_at = fields.DatetimeField(null=True)
    
    ocr_data = fields.JSONField(null=True)
    extracted_data = fields.JSONField(null=True)
    
    is_primary = fields.BooleanField(default=False, index=True)
    is_public = fields.BooleanField(default=False)
    
    access_token = fields.CharField(max_length=64, null=True, unique=True, index=True)
    access_expires_at = fields.DatetimeField(null=True)
    
    watermark_text = fields.CharField(max_length=255, null=True)
    
    storage_provider = fields.CharField(max_length=50, default='local')
    storage_bucket = fields.CharField(max_length=100, null=True)
    storage_key = fields.CharField(max_length=255, null=True)
    
    thumbnail_path = fields.TextField(null=True)
    thumbnail_url = fields.TextField(null=True)
    
    class Meta:
        table = "documents"
        indexes = [
            ("document_number",),
            ("uploaded_by_id", "document_type"),
            ("uploaded_by_id", "verification_status"),
            ("uploaded_by_id", "is_primary"),
            ("file_hash",),
            ("access_token",),
            ("expires_at", "document_status"),
        ]
        ordering = ["-uploaded_at"]

    @property
    def file_extension(self) -> str:
        return Path(self.original_filename).suffix.lower()

    @property
    def is_image(self) -> bool:
        return self.mime_type and self.mime_type.startswith('image/')

    @property
    def is_pdf(self) -> bool:
        return self.mime_type == 'application/pdf'

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def can_access(self) -> bool:
        if not self.access_expires_at:
            return True
        return datetime.utcnow() <= self.access_expires_at

    @property
    def file_info(self) -> Dict[str, Any]:
        return {
            "filename": self.original_filename,
            "size": self.file_size,
            "type": self.mime_type,
            "extension": self.file_extension,
            "uploaded_at": self.uploaded_at,
            "is_expired": self.is_expired
        }

    async def generate_access_token(self, hours: int = 24) -> str:
        import secrets
        token = secrets.token_urlsafe(48)
        self.access_token = token
        self.access_expires_at = datetime.utcnow() + timedelta(hours=hours)
        await self.save(update_fields=["access_token", "access_expires_at"])
        return token

    async def verify_document(self, admin_user, notes: str = ""):
        self.verification_status = VerificationStatus.VERIFIED
        self.verified_by = admin_user
        self.verified_at = datetime.utcnow()
        self.verification_notes = notes
        await self.save(update_fields=[
            "verification_status",
            "verified_by",
            "verified_at",
            "verification_notes"
        ])

    async def reject_document(self, reason: str, admin_user=None):
        self.verification_status = VerificationStatus.REJECTED
        self.rejection_reason = reason
        if admin_user:
            self.verified_by = admin_user
            self.verified_at = datetime.utcnow()
        await self.save(update_fields=[
            "verification_status",
            "rejection_reason",
            "verified_by",
            "verified_at"
        ])

    async def set_as_primary(self):
        await IdentityDocument.filter(
            uploaded_by=self.uploaded_by,
            document_type=self.document_type,
            is_primary=True
        ).update(is_primary=False)
        
        self.is_primary = True
        await self.save(update_fields=["is_primary"])

    async def generate_watermark(self, text: Optional[str] = None):
        if text:
            self.watermark_text = text
        elif not self.watermark_text:
            self.watermark_text = f"User ID: {self.uploaded_by_id} | Document ID: {self.id}"
        
        await self.save(update_fields=["watermark_text"])





# ============== EXAMPLE USAGE ==============

# async def example_usage():
#     """Example of how to use the document functions"""
    
#     # Import your User model
#     from .user import User
    
#     # 1. Save a document
#     with open("path/to/document.jpg", "rb") as f:
#         document = await DocumentManager.save_document(
#             file_data=f,
#             filename="my_id_card.jpg",
#             user_id="user-uuid-here",
#             document_type=DocumentType.NATIONAL_ID,
#             document_number="A12345678",
#             metadata={"country": "KE", "issue_date": "2024-01-01"},
#             is_public=False
#         )
    
#     print(f"Document saved with ID: {document.id}")
#     print(f"File path: {document.file_path}")
#     print(f"File URL: {document.file_url}")
    
#     # 2. Get a document by ID
#     retrieved_doc = await DocumentManager.get_document_by_id(str(document.id))
#     if retrieved_doc:
#         print(f"Retrieved document: {retrieved_doc.original_filename}")
    
#     # 3. Get document file
#     try:
#         file_info = await DocumentManager.get_document_file(str(document.id))
#         if file_info:
#             file_path, mime_type = file_info
#             print(f"File exists at: {file_path}")
#             print(f"MIME type: {mime_type}")
#     except (PermissionError, FileNotFoundError) as e:
#         print(f"Error: {e}")
    
#     # 4. Generate access token for temporary access
#     token = await document.generate_access_token(hours=24)
#     print(f"Access token: {token}")
    
#     # 5. Get document with token
#     doc_with_token = await DocumentManager.get_document_with_token(
#         str(document.id),
#         token
#     )
    
#     # 6. Get user's documents
#     user_docs = await DocumentManager.get_user_documents(
#         user_id="user-uuid-here",
#         document_type=DocumentType.NATIONAL_ID,
#         verification_status=VerificationStatus.VERIFIED
#     )
    
#     # 7. Delete a document
#     await DocumentManager.delete_document(str(document.id))