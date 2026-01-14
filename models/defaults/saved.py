from tortoise.models import Model
from tortoise import fields
import uuid
from typing import Optional, Any
from enum import IntEnum
from datetime import datetime


class SaveStatus(IntEnum):
    """Status of saved item"""
    ACTIVE = 1
    ARCHIVED = 2
    DELETED = 3
    EXPIRED = 4


class BaseSavedItem(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    user = fields.ForeignKeyField(
        'models.User',
        related_name='saved_items',
        on_delete=fields.CASCADE,
        index=True
    )
    
    item_id = fields.CharField(max_length=100, index=True)
    notes = fields.TextField(null=True)
    status = fields.IntEnumField(SaveStatus, default=SaveStatus.ACTIVE, index=True)
    
    is_pinned = fields.BooleanField(default=False, index=True)
    is_private = fields.BooleanField(default=True, index=True)
    shared_with = fields.JSONField(default=list)  # List of user IDs
    expires_at = fields.DatetimeField(null=True, index=True)
    
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    archived_at = fields.DatetimeField(null=True)
    
    # Analytics
    view_count = fields.IntField(default=0)
    last_viewed_at = fields.DatetimeField(null=True)
    
    folder_name = fields.CharField(max_length=100, null=True, default="General")
    
    class Meta:
        abstract = True
        indexes = [
            ("user_id", "item_type", "item_id"), 
            ("user_id", "status"),
            ("user_id", "folder_name"),
            ("user_id", "is_pinned"),
            ("user_id", "created_at"),
            ("item_type", "item_id", "status"), 
        ]
        ordering = ["-is_pinned", "-created_at"]
    
    @property
    def is_expired(self) -> bool:
        """Check if the saved item has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Check if the saved item is active"""
        return self.status == SaveStatus.ACTIVE and not self.is_expired
    
    async def archive(self):
        """Archive the saved item"""
        self.status = SaveStatus.ARCHIVED
        self.archived_at = datetime.utcnow()
        await self.save(update_fields=["status", "archived_at"])
    
    async def restore(self):
        """Restore archived item"""
        self.status = SaveStatus.ACTIVE
        self.archived_at = None
        await self.save(update_fields=["status", "archived_at"])
    
    async def increment_view(self):
        """Increment view count"""
        self.view_count += 1
        self.last_viewed_at = datetime.utcnow()
        await self.save(update_fields=["view_count", "last_viewed_at"])
    
    async def pin(self):
        """Pin the item"""
        self.is_pinned = True
        await self.save(update_fields=["is_pinned"])
    
    async def unpin(self):
        """Unpin the item"""
        self.is_pinned = False
        await self.save(update_fields=["is_pinned"])
    
    async def add_tag(self, tag: str):
        """Add a tag to the saved item"""
        if tag not in self.tags:
            self.tags.append(tag)
            await self.save(update_fields=["tags"])
    
    async def share_with_user(self, user_id: str):
        """Share saved item with another user"""
        if user_id not in self.shared_with:
            self.shared_with.append(user_id)
            await self.save(update_fields=["shared_with"])
    
    @classmethod
    async def get_user_saved_items(
        cls,
        user_id: str,
        folder: Optional[str] = None,
        pinned_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ):
        """Get saved items for a user with filtering options"""
        query = cls.filter(
            user_id=user_id,
            status=SaveStatus.ACTIVE
        )
        
        if folder:
            query = query.filter(folder_name=folder)
        
        if pinned_only:
            query = query.filter(is_pinned=True)
        
        return await query.order_by("-created_at").offset(offset).limit(limit).all()