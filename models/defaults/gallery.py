from tortoise import fields, Model
from uuid import uuid4
from enum import Enum

class FileType(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"

class BaseGallery(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=200, null=True)  # also alt text
    description = fields.TextField(null=True)  # also caption
    image_url = fields.CharField(max_length=500)
    file_type = fields.CharEnumField(FileType, default=FileType.IMAGE)
    mime_type = fields.CharField(max_length=100, null=True)
    file_size = fields.FloatField(null=True)

    is_primary = fields.BooleanField(default=False)
    is_featured = fields.BooleanField(default=False)
    sort_order = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["sort_order", "created_at"]
