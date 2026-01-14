from tortoise.models import Model
from tortoise import fields
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import IntEnum


class ReplyStatus(IntEnum):
    """Status of review replies"""
    ACTIVE = 1
    DELETED = 2
    HIDDEN = 3
    REPORTED = 4
    EDITED = 5


class ReviewReply(Model):
    """
    Model for replies to reviews.
    Allows users (including review owners) to reply to reviews.
    """
    
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    
    author = fields.ForeignKeyField(
        'models.User',
        related_name='review_reply',
        on_delete=fields.CASCADE,
        index=True
    )
    
    parent_reply = fields.ForeignKeyField(
        'models.ReviewReply',
        related_name='child_replies',
        on_delete=fields.CASCADE,
        index=True
    )
    
    content = fields.TextField()
    
    status = fields.IntEnumField(ReplyStatus, default=ReplyStatus.ACTIVE, index=True)
    
    moderated_by = fields.ForeignKeyField(
        'models.AdminUser',
        related_name='moderated_replies',
        null=True,
        on_delete=fields.SET_NULL
    )
    moderated_at = fields.DatetimeField(null=True)
    moderation_notes = fields.TextField(null=True)
    
    # Engagement metrics
    likes_count = fields.IntField(default=0, index=True)
    helpful_count = fields.IntField(default=0, index=True)
    report_count = fields.IntField(default=0)
    
    # Report tracking
    reported_by = fields.JSONField(default=list) 
    
    is_author_response = fields.BooleanField(default=False, index=True)  # If reply is from review owner
    is_edited = fields.BooleanField(default=False, index=True)
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)
    
    edit_history = fields.JSONField(default=list)
    
    class Meta:
        table = "review_replies"
        indexes = [
            # ("review_id", "created_at"),
            # ("review_id", "status"),
            ("author_id", "created_at"),
            ("parent_reply_id", "created_at"),
            ("is_author_response", "status"),
            ("likes_count", "created_at"),
        ]
        ordering = ["created_at"]  # Oldest first for threaded conversations
    
    @property
    def is_active(self) -> bool:
        """Check if reply is active and visible"""
        return self.status == ReplyStatus.ACTIVE
    
    @property
    def is_deleted(self) -> bool:
        """Check if reply is deleted"""
        return self.status == ReplyStatus.DELETED
    
    @property
    def is_nested(self) -> bool:
        """Check if this is a nested reply (reply to a reply)"""
        return self.parent_reply_id is not None
    
    @property
    def depth_level(self) -> int:
        """Get the depth level in the reply thread"""
        if not self.parent_reply_id:
            return 1
        # In practice, you might want to calculate this recursively
        return 2  # For simplicity, assume max depth of 2
    
    async def add_like(self, user_id: str) -> bool:
        """Add a like to the reply"""
        # In production, you'd track unique likes in a separate table
        self.likes_count += 1
        await self.save(update_fields=["likes_count"])
        return True
    
    async def mark_helpful(self, user_id: str) -> bool:
        """Mark reply as helpful"""
        self.helpful_count += 1
        await self.save(update_fields=["helpful_count"])
        return True
    
    async def edit_content(self, new_content: str, editor_id: Optional[str] = None):
        """Edit reply content with history tracking"""
        # Save old content to history
        self.edit_history.append({
            "old_content": self.content,
            "new_content": new_content,
            "edited_by": editor_id,
            "edited_at": datetime.utcnow().isoformat()
        })
        
        # Update content
        self.content = new_content
        self.is_edited = True
        self.status = ReplyStatus.EDITED if self.status == ReplyStatus.ACTIVE else self.status
        
        await self.save(update_fields=[
            "content", "is_edited", "status", "edit_history", "updated_at"
        ])
    
    async def delete(self, soft_delete: bool = True):
        """Delete the reply"""
        if soft_delete:
            self.status = ReplyStatus.DELETED
            self.deleted_at = datetime.utcnow()
            await self.save(update_fields=["status", "deleted_at"])
        else:
            await super().delete()
    
    async def restore(self):
        """Restore a deleted reply"""
        self.status = ReplyStatus.ACTIVE
        self.deleted_at = None
        await self.save(update_fields=["status", "deleted_at"])
    
    async def hide(self, moderator_id: Optional[str] = None, reason: Optional[str] = None):
        """Hide the reply (moderator action)"""
        self.status = ReplyStatus.HIDDEN
        
        if moderator_id:
            self.moderated_by_id = moderator_id
            self.moderated_at = datetime.utcnow()
            self.moderation_notes = reason
        
        await self.save(update_fields=[
            "status", "moderated_by_id", "moderated_at", "moderation_notes"
        ])
    
    async def report(self, user_id: str, reason: str):
        """Report the reply"""
        if user_id not in self.reported_by:
            self.reported_by.append(user_id)
        
        self.report_count += 1
        self.status = ReplyStatus.REPORTED
        
        # Store report details
        if 'reports' not in self.edit_history:
            self.edit_history = []
        
        self.edit_history.append({
            'type': 'report',
            'user_id': user_id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        await self.save(update_fields=[
            "reported_by", "report_count", "status", "edit_history"
        ])
    
    async def create_nested_reply(self, author_id: str, content: str) -> 'ReviewReply':
        """Create a nested reply to this reply"""
        from .review_reply import ReviewReply  # Avoid circular import
        
        nested_reply = await ReviewReply.create(
            review_id=self.review_id,
            author_id=author_id,
            parent_reply_id=self.id,
            content=content
        )
        
        return nested_reply
    
    async def get_thread_replies(self, include_self: bool = False) -> List['ReviewReply']:
        """Get all replies in this thread (replies to replies)"""
        query = ReviewReply.filter(
            review_id=self.review_id
        ).order_by("created_at")
        
        replies = await query.all()
        
        if include_self:
            return replies
        
        # Filter to only replies in this thread
        thread_replies = []
        for reply in replies:
            # Check if this reply is in the thread starting from self
            if self._is_in_thread(reply, self.id):
                thread_replies.append(reply)
        
        return thread_replies
    
    def _is_in_thread(self, reply: 'ReviewReply', thread_start_id: str) -> bool:
        """Helper to check if a reply is in a thread"""
        current = reply
        while current.parent_reply_id:
            if current.parent_reply_id == thread_start_id:
                return True
            # In practice, you'd fetch the parent reply here
            # This is simplified
            break
        return False
    
    @classmethod
    async def get_review_replies(
        cls,
        review_id: str,
        include_nested: bool = True,
        only_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List['ReviewReply']:
        """Get all replies for a review"""
        query = cls.filter(review_id=review_id)
        
        if only_active:
            query = query.filter(status=ReplyStatus.ACTIVE)
        
        if not include_nested:
            query = query.filter(parent_reply_id=None)
        
        return await query.order_by("created_at").offset(offset).limit(limit).all()
    
    @classmethod
    async def get_user_replies(
        cls,
        user_id: str,
        only_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List['ReviewReply']:
        """Get all replies by a user"""
        query = cls.filter(author_id=user_id)
        
        if only_active:
            query = query.filter(status=ReplyStatus.ACTIVE)
        
        return await query.order_by("-created_at").offset(offset).limit(limit).all()