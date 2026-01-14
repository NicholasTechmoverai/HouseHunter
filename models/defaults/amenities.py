import uuid
from tortoise import fields, Model

import re
import uuid
from typing import Optional
from tortoise.models import Model
from tortoise import fields


class BaseAmenity(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=100, index=True)
    slug = fields.CharField(max_length=50, null=True)
    description = fields.TextField(null=True)
    icon = fields.CharField(max_length=100, null=True)
    sort_order = fields.IntField(default=0)
    is_featured = fields.BooleanField(default=False, index=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    @classmethod
    def generate_slug(cls, name: str, max_length: int = 50) -> str:
        """
        Generate a URL-friendly slug from a name.
        
        Args:
            name: The name to convert to slug
            max_length: Maximum length for the slug (default: 50)
            
        Returns:
            A URL-friendly slug string
        """
        if not name:
            raise ValueError("Name cannot be empty")
        
        # Convert to lowercase
        slug = name.lower()
        
        # Remove special characters, keep letters, numbers, spaces, and hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        
        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        
        # Remove multiple hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Trim hyphens from start and end
        slug = slug.strip('-')
        
        # Truncate to max length if needed
        if len(slug) > max_length:
            # Try to truncate at a hyphen
            truncated = slug[:max_length]
            last_hyphen = truncated.rfind('-')
            if last_hyphen > 0:
                slug = truncated[:last_hyphen]
            else:
                slug = truncated
        
        return slug
    
    @classmethod
    async def generate_unique_slug(cls, name: str, exclude_id: Optional[str] = None) -> str:
        """
        Generate a unique slug, ensuring it doesn't already exist in the database.
        
        Args:
            name: The base name to generate slug from
            exclude_id: Optional ID to exclude from uniqueness check (for updates)
            
        Returns:
            A unique slug string
        """
        base_slug = cls.generate_slug(name)
        
        # Check if slug already exists
        query = cls.filter(slug=base_slug)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        if not await query.exists():
            return base_slug
        
        # If slug exists, add suffix
        counter = 1
        while True:
            new_slug = f"{base_slug}-{counter}"
            query = cls.filter(slug=new_slug)
            if exclude_id:
                query = query.exclude(id=exclude_id)
            
            if not await query.exists():
                return new_slug
            
            counter += 1
    
    async def save(self, *args, **kwargs) -> None:
        """
        Override save to auto-generate slug if not provided.
        """
        if not self.slug and self.name:
            self.slug = await self.__class__.generate_unique_slug(self.name)
        
        await super().save(*args, **kwargs)
    
    async def update_slug(self) -> None:
        """
        Update the slug based on current name.
        Useful when name changes and slug needs to be regenerated.
        """
        if self.name:
            self.slug = await self.__class__.generate_unique_slug(
                self.name, 
                exclude_id=str(self.id)
            )
            await self.save()
    
    class Meta:
        abstract = True
        
        
        
class AmenityCategory(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    name = fields.CharField(max_length=100, unique=True)
    slug = fields.CharField(max_length=50, unique=True, null=True)  # e.g., "entertainment"
    description = fields.TextField(null=True)
    is_free  = fields.BooleanField(null=True)
    icon = fields.CharField(max_length=100, null=True)
    sort_order = fields.IntField(default=0)

    class Meta:
        table = "amenity_categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name
