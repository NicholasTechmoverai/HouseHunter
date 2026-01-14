from tortoise.models import Model
from tortoise import fields
import uuid
from typing import Optional, Dict, Any, List
from enum import IntEnum
from datetime import datetime

class ReviewType(IntEnum):
    """Types of reviews in the system."""
    PROPERTY = 1
    RENTAL = 2
    SWAP = 3
    LANDLORD = 4
    TENANT = 5
    SERVICE = 6
    PRODUCT = 7
    COMPANY = 8
    AGENT = 9
    CONTRACTOR = 10
    EVENT = 11
    CONTENT = 12


class ReviewStatus(IntEnum):
    """Status of reviews"""
    PENDING = 1      # Waiting for approval
    APPROVED = 2     # Published and visible
    REJECTED = 3     # Rejected by moderators
    HIDDEN = 4       # Hidden from public view
    DELETED = 5      # Soft deleted
    REPORTED = 6     # Reported for review
    EDITED = 7       # Edited by user/moderator


class Review(Model):
    """
    Abstract base model for reviews and ratings.
    Supports star ratings, text reviews, and helpfulness votes.
    """
    
    id = fields.UUIDField(pk=True, default=uuid.uuid4, editable=False)
    
    reviewer = fields.ForeignKeyField(
        'models.User',
        related_name='submitted_reviews',
        on_delete=fields.CASCADE,
        index=True
    )
    
    review_type = fields.IntEnumField(ReviewType, index=True)
    item_id = fields.CharField(max_length=100, index=True)
    
    item_owner = fields.ForeignKeyField(
        'models.User',
        related_name='received_reviews',
        null=True,
        on_delete=fields.SET_NULL,
        index=True
    )
    
    # Rating (1-5 stars)
    rating = fields.IntField(default=1, index=True)
    
    title = fields.CharField(max_length=200, null=True)
    content = fields.TextField()
    pros = fields.JSONField(default=list)  # List of pros
    cons = fields.JSONField(default=list)  # List of cons
    
    is_edited = fields.BooleanField(default=False)
    edited_at = fields.DatetimeField(null=True)

    
    # Verification
    is_verified_purchase = fields.BooleanField(default=False, index=True)
    verification_data = fields.JSONField(null=True)  # Proof of transaction/experience
    
    status = fields.IntEnumField(ReviewStatus, default=ReviewStatus.APPROVED, index=True)
    
    moderated_by = fields.ForeignKeyField(
        'models.AdminUser',
        related_name='moderated_reviews',
        null=True,
        on_delete=fields.SET_NULL
    )
    moderated_at = fields.DatetimeField(null=True)
    moderation_notes = fields.TextField(null=True)
    rejection_reason = fields.TextField(null=True)
    
    helpful_count = fields.IntField(default=0, index=True)
    not_helpful_count = fields.IntField(default=0)
    reply_count = fields.IntField(default=0)
   
    
    report_count = fields.IntField(default=0)
    reported_by = fields.JSONField(default=list) 
    report_reason = fields.TextField(null=True)

    liked_by = fields.JSONField(default=list)
    disliked_by = fields.JSONField(default=list)
    likes_count = fields.IntField(default=0)
    dislike_count = fields.IntField(default=0)
    
    metadata = fields.JSONField(default=dict)
    tags = fields.JSONField(default=list)
    
    first_experience_date = fields.DateField(null=True)    
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    published_at = fields.DatetimeField(null=True, index=True)
    deleted_at = fields.DatetimeField(null=True)
    
    is_anonymous = fields.BooleanField(default=False, index=True)
    
    # Featured/helpful
    is_featured = fields.BooleanField(default=False, index=True)
    is_editor_pick = fields.BooleanField(default=False, index=True)
    
    # Language/locale
    language = fields.CharField(max_length=10, default='en')
    
    class Meta:
        table = "reviews"
        indexes = [
            ("reviewer_id", "review_type", "item_id"),  # One review per user per item
            ("item_id", "review_type", "status"),
            ("item_id", "review_type", "rating"),
            ("item_id", "review_type", "created_at"),
            ("rating", "status"),
            ("helpful_count", "status"),
            ("is_featured", "status"),
            ("published_at", "status"),
            ("item_owner_id", "status"),
        ]
        ordering = ["-is_featured", "-helpful_count", "-created_at"]
    
    @property
    def average_rating(self) -> float:
        """Get the rating as float (for calculations)"""
        return float(self.rating)
    
    @property
    def is_published(self) -> bool:
        """Check if review is published and visible"""
        return self.status == ReviewStatus.APPROVED
    
    @property
    def is_reported(self) -> bool:
        """Check if review has been reported"""
        return self.status == ReviewStatus.REPORTED or self.report_count > 0
    
    @property
    def reviewer_name(self) -> str:
        """Get reviewer name (anonymous or real)"""
        if self.is_anonymous:
            return "Anonymous User"
        return self.reviewer.full_name if hasattr(self.reviewer, 'full_name') else "User"
    
    async def approve(self, moderator_id: Optional[str] = None):
        """Approve and publish the review"""
        self.status = ReviewStatus.APPROVED
        self.published_at = datetime.utcnow()
        
        if moderator_id:
            self.moderated_by_id = moderator_id
            self.moderated_at = datetime.utcnow()
        
        await self.save(update_fields=[
            "status", "published_at", "moderated_by_id", "moderated_at"
        ])
    
    async def reject(self, reason: str, moderator_id: Optional[str] = None):
        """Reject the review"""
        self.status = ReviewStatus.REJECTED
        self.rejection_reason = reason
        
        if moderator_id:
            self.moderated_by_id = moderator_id
            self.moderated_at = datetime.utcnow()
        
        await self.save(update_fields=[
            "status", "rejection_reason", "moderated_by_id", "moderated_at"
        ])
    
    async def mark_helpful(self, user_id: str):
        """Mark review as helpful by a user"""
        # Track unique helpful votes (simplified - would need separate model for production)
        self.helpful_count += 1
        await self.save(update_fields=["helpful_count"])
    
    async def mark_not_helpful(self, user_id: str):
        """Mark review as not helpful by a user"""
        self.not_helpful_count += 1
        await self.save(update_fields=["not_helpful_count"])
    
    async def report(self, user_id: str, reason: str):
        """Report the review"""
        if user_id not in self.reported_by:
            self.reported_by.append(user_id)
        
        self.report_count += 1
        self.status = ReviewStatus.REPORTED
        
        # Store report reason in metadata
        if 'reports' not in self.metadata:
            self.metadata['reports'] = []
        
        self.metadata['reports'].append({
            'user_id': user_id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        await self.save(update_fields=[
            "reported_by", "report_count", "status", "metadata"
        ])
    
    async def add_owner_response(self, response: str, owner_id: str):
        """Add owner response to review"""
        self.owner_response = response
        self.owner_response_at = datetime.utcnow()
        self.item_owner_id = owner_id
        await self.save(update_fields=[
            "owner_response", "owner_response_at", "item_owner_id"
        ])
        
        
    async def add_like(self, user_id):
        """Add a like from a user."""
        if user_id in self.liked_by:
            return

        if user_id in self.disliked_by:
            self.disliked_by.remove(user_id)

        self.liked_by.append(user_id)
        self.likes_count = len(self.liked_by)
        self.dislike_count = len(self.disliked_by)

        await self.save(update_fields=["likes_count", "dislike_count", "liked_by", "disliked_by"])


    async def add_dislike(self, user_id):
        """Add a dislike from a user."""
        if user_id in self.disliked_by:
            return

        if user_id in self.liked_by:
            self.liked_by.remove(user_id)

        self.disliked_by.append(user_id)
        self.likes_count = len(self.liked_by)
        self.dislike_count = len(self.disliked_by)

        await self.save(update_fields=["likes_count", "dislike_count", "liked_by", "disliked_by"])

            
    
    async def add_tag(self, tag: str):
        """Add a tag to the review"""
        if tag not in self.tags:
            self.tags.append(tag)
            await self.save(update_fields=["tags"])
    
    async def feature(self):
        """Feature the review (mark as important/helpful)"""
        self.is_featured = True
        await self.save(update_fields=["is_featured"])
    
    async def unfeature(self):
        """Remove featured status"""
        self.is_featured = False
        await self.save(update_fields=["is_featured"])
    
    @classmethod
    async def calculate_average_rating(
        cls,
        item_id: str,
        review_type: ReviewType
    ) -> Dict[str, Any]:
        """Calculate average rating and statistics for an item"""
        reviews = await cls.filter(
            item_id=item_id,
            review_type=review_type,
            status=ReviewStatus.APPROVED
        ).all()
        
        if not reviews:
            return {
                "average": 0,
                "count": 0,
                "distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "total_helpful": 0
            }
        
        total = len(reviews)
        ratings_sum = sum(r.rating for r in reviews)
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for review in reviews:
            distribution[review.rating] += 1
        
        return {
            "average": round(ratings_sum / total, 1),
            "count": total,
            "distribution": distribution,
            "total_helpful": sum(r.helpful_count for r in reviews),
            "featured_count": sum(1 for r in reviews if r.is_featured)
        }