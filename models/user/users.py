from tortoise.models import Model
from tortoise import fields
from tortoise.validators import RegexValidator
from typing import Optional
import uuid

from .base_user import BaseUser

class User(BaseUser):
    bio = fields.TextField(null=True)
    tagline = fields.CharField(max_length=200, null=True)
    website = fields.CharField(
        max_length=255, 
        null=True, 
        validators=[RegexValidator(r'^https?://', 0)]
    )
    
    occupation = fields.CharField(max_length=100, null=True)
    company = fields.CharField(max_length=100, null=True)
    job_title = fields.CharField(max_length=100, null=True)
    industry = fields.CharField(max_length=100, null=True)
    
    current_city = fields.CharField(max_length=100, null=True)
    current_county = fields.CharField(max_length=100, null=True)
    current_country = fields.CharField(max_length=100, null=True)
    current_postal_code = fields.CharField(max_length=20, null=True)
    current_address = fields.TextField(null=True)
    current_latitude = fields.FloatField(null=True)
    current_longitude = fields.FloatField(null=True)

    home_city = fields.CharField(max_length=100, null=True)
    home_county = fields.CharField(max_length=100, null=True)
    home_country = fields.CharField(max_length=100, null=True)
    home_latitude = fields.FloatField(null=True)
    home_longitude = fields.FloatField(null=True)
    
    social_links = fields.JSONField(default=dict)
    
    profile_views = fields.IntField(default=0)
    property_views = fields.IntField(default=0)
    search_count = fields.IntField(default=0)
    # favorite_properties = fields.IntField(default=0)
    
    wallet_balance = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_spent = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_earned = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    subscription_tier = fields.CharField(max_length=50, null=True)
    subscription_start = fields.DatetimeField(null=True)
    subscription_end = fields.DatetimeField(null=True)
    subscription_auto_renew = fields.BooleanField(default=False)
    
    
    categories_of_interest = fields.JSONField(default=list)
    
    class Meta:
        table = "users"
        indexes = [
            ("current_city",),
            ("current_country",),
            ("occupation",),
            ("subscription_tier",),
            ("wallet_balance",),
            ("home_latitude", "home_longitude"),
        ]
    
    async def save(self, *args, **kwargs):
        creating = not self._saved_in_db

        if creating:
            if not self.public_id:
                self.public_id = await self.__class__.generate_unique_public_id("USR")

            if not self.username:
                self.username = await self.__class__.generate_unique_username(
                    self.first_name,
                    self.last_name
                )

            if not self.referral_code:
                self.referral_code = await self.__class__.generate_unique_referral_code("REF")

        await super().save(*args, **kwargs)

    
    
    @property
    def is_premium(self):
        return self.subscription_tier in ["premium", "pro", "enterprise"]
    
    def to_dict(self):
        base_dict = super().to_dict()
        user_dict = {
            "bio": self.bio,
            "tagline": self.tagline,
            "website": self.website,
            "occupation": self.occupation,
            "company": self.company,
            "job_title": self.job_title,
            "industry": self.industry,
            "current_city": self.current_city,
            "current_county": self.current_county,
            "current_country": self.current_country,
            "current_postal_code": self.current_postal_code,
            "home_city": self.home_city,
            "home_country": self.home_country,
            "home_latitude": float(self.home_latitude) if self.home_latitude else None,
            "home_longitude": float(self.home_longitude) if self.home_longitude else None,
            "current_county": self.current_county,
            "current_address": self.current_address,
            "current_latitude": float(self.current_latitude) if self.current_latitude else None,
            "current_longitude": float(self.current_longitude) if self.current_longitude else None,
            "social_links": self.social_links,
            "profile_views": self.profile_views,
            "property_views": self.property_views,
            "search_count": self.search_count,
            "wallet_balance": float(self.wallet_balance),
            "total_spent": float(self.total_spent),
            "total_earned": float(self.total_earned),
            "subscription_tier": self.subscription_tier,
            "subscription_start": self.subscription_start.isoformat() if self.subscription_start else None,
            "subscription_end": self.subscription_end.isoformat() if self.subscription_end else None,
            "subscription_auto_renew": self.subscription_auto_renew,
            "categories_of_interest": self.categories_of_interest,
            "is_premium": self.is_premium,
        }
        return {**base_dict, **user_dict}