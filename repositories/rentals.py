from typing import Optional, Dict, Any, List, Union
from uuid import UUID
import random
import re
from datetime import datetime
from decimal import Decimal
from math import cos

from tortoise.exceptions import DoesNotExist, IntegrityError,ValidationError
from tortoise.expressions import Q
from core.settings import settings

from models.for_rent.rental import RentalComplex, RentalStatus
from models.for_rent.gallery import RentalGallery
from models.for_rent.amenities import RentalAmenity
from models.for_rent.rules import RentalRules
from models.for_rent.pricing import RentalPricing, RentalPricingExtraFees


from models.defaults.property_catogories import PropertyCategory
from tortoise.transactions import in_transaction
from models.user import User
from schemas.request.rental import RentalCreate,HeadInfoCreate,LocationCreate,AmenityCreate,PriceCreate,PropertyRuleCreate
from utils.image_save import save_base64_image
from core.logger import setup_logger
logger = setup_logger()


class RentalRepository:
    def __init__(self, model=RentalComplex):
        self.model = model

    # Basic Getters
    async def get_by_id(self, rental_id: str) -> Optional[RentalComplex]:
        """Get rental by its ID."""
        return await self.model.get_or_none(id=rental_id)
    async def get_by_id_with_owner_check(
        self, 
        rental_id: str, 
        user_id: str
        ) -> RentalComplex:
            """
            Get rental by ID with owner permission check.
            Raises DoesNotExist if rental not found.
            Raises PermissionError if user is not the owner.
            """
            rental = await self.model.get_or_none(id=rental_id)
            
            if not rental:
                raise DoesNotExist(f"Rental with ID {rental_id} not found")
            
            if rental.publisher_id != user_id:
                raise PermissionError("User is not the owner of this rental")
            
            return rental

    async def get_by_slug(self, slug: str) -> Optional[RentalComplex]:
        """Get rental by its slug."""
        return await self.model.get_or_none(slug=slug)

    async def get_by_user(self, user_id: str, include_deleted: bool = False) -> List[RentalComplex]:
        """Get all rentals owned by a specific user."""
        query = self.model.filter(publisher_id=user_id)
        if not include_deleted:
            query = query.filter(is_deleted=False)
        return await query.all()

    async def get_managed_by_user(self, user_id: str) -> List[RentalComplex]:
        """Get all rentals managed by a user."""
        return await self.model.filter(managers__id=user_id).all()

    async def check_user_owns_rental(self, user_id: str, rental_id: str) -> bool:
        """Check if user owns a specific rental."""
        return await self.model.filter(id=rental_id, publisher_id=user_id).exists()
    
    async def save_head_info(
        self, 
        user_id: str, 
        rental_id: str,
        payload: HeadInfoCreate, 
        existing_rental: Optional[RentalComplex] = None
    ) -> RentalComplex:
        """
        Create or update rental property head info.
        Uses existing_rental object if available to avoid extra query.
        """
        rental_data = payload.model_dump(exclude_none=True)
        
        # Handle profile picture
        if rental_data.get('profile_picture'):
            profile_url = await save_base64_image(base64_str=rental_data['profile_picture'],folder='rentals',subfolder='cover')
            rental_data['profile_picture'] = profile_url
        
        rental_data['publisher_id'] = user_id
        # rental_data['category'] = 20
        
        if existing_rental:
            # UPDATE MODE (using existing object)
            # Regenerate slug only if title changed
            if 'title' in rental_data and existing_rental.title != rental_data['title']:
                base_slug = self.model.generate_slug(rental_data['title'])
                rental_data['slug'] = await self._generate_unique_slug(
                    base_slug, 
                    exclude_id=rental_id  # Exclude current rental from slug check
                )
            
            # Update fields
            for key, value in rental_data.items():
                setattr(existing_rental, key, value)
            
            await existing_rental.save()
            return existing_rental
            
        else:
            # CREATE MODE
            rental_data['id'] = rental_id
            
            # Generate slug for new rental
            if 'title' in rental_data and not rental_data.get('slug'):
                base_slug = self.model.generate_slug(rental_data['title'])
                rental_data['slug'] = await self._generate_unique_slug(base_slug)
            
            try:
                rental = await self.model.create(**rental_data)
                return rental
            except IntegrityError as e:
                if 'slug' in str(e).lower():
                    # Retry with different slug
                    rental_data['slug'] = f"{base_slug}-{random.randint(1000, 9999)}"
                    rental = await self.model.create(**rental_data)
                    return rental
                raise e

    async def _generate_unique_slug(
        self, 
        base_slug: str, 
        exclude_id: Optional[str] = None
    ) -> str:
        """Generate a unique slug, optionally excluding a specific ID."""
        counter = 1
        slug = base_slug
        
        while True:
            query = self.model.filter(slug=slug)
            if exclude_id:
                query = query.exclude(id=exclude_id)
            
            if not await query.exists():
                return slug
            
            slug = f"{base_slug}-{counter}"
            counter += 1

    async def addGallery(self, gallery_data: dict) -> dict:
        """Add a single gallery item"""
        return await RentalGallery.create(**gallery_data)
    
    async def addGalleryBatch(self, gallery_items: list[dict]) -> list[dict]:
        """Add multiple gallery items at once"""
        created_items = []
        for item in gallery_items:
            gallery_item = await RentalGallery.create(**item)
            created_items.append(gallery_item)
        return created_items

    async def save_location_info(
        self, 
        user_id: str, 
        rental_id: str,
        payload: HeadInfoCreate, 
        existing_rental: Optional[RentalComplex] = None
    ) -> dict:
        """Save location info - returns {success, message, data}"""
        
        if not existing_rental:
            return {
                "success": False,
                "message": "Rental not found. Create rental first.",
                "data": None
            }
        
        if str(existing_rental.publisher_id) != user_id:
            return {
                "success": False,
                "message": "Permission denied",
                "data": None
            }
        
        try:
            rental_data = payload.model_dump(exclude_unset=True)
            
            if not rental_data.get('city') or not rental_data.get('address'):
                return {
                    "success": False,
                    "message": "City and address required",
                    "data": None
                }
            
            coordinates = rental_data.get('coordinates', {}) 

            rental_data['longitude'] = coordinates.get('long')  
            rental_data['latitude'] = coordinates.get('lat') 

            location_fields = ['country', 'state', 'city', 'address', 'longitude', 'latitude']
            for field in location_fields:
                if field in rental_data:
                    setattr(existing_rental, field, rental_data[field])
            
            # existing_rental.location_updated_at = datetime.now()
            await existing_rental.save()
            
            return {
                "success": True,
                "message": "Location saved successfully",
                "data": existing_rental
            }
            
        except Exception as e:
            logger.error(f"Error saving location: {e}")
            return {
                "success": False,
                "message": "Failed to save location",
                "data": None
            }

    async def save_amenities(
        self,
        rental_id: str,
        payload: list[AmenityCreate],
        existing_rental: RentalComplex,
    ) -> dict:

        if not existing_rental:
            return {
                "success": False,
                "message": "Rental not found",
                "data": None,
            }

        # Empty payload → clear amenities
        if not payload:
            await RentalAmenity.filter(rental=existing_rental).delete()
            return {
                "success": True,
                "message": "Amenities cleared",
                "data": [],
            }

        try:
            async with in_transaction():

                # Remove existing amenities
                await RentalAmenity.filter(rental=existing_rental).delete()

                amenities = []

                for item in payload:
                    data = item.model_dump()

                    name = (data.get("name") or "").strip()
                    if not name:
                        continue

                    amenity = RentalAmenity(
                        rental=existing_rental,
                        name=name,
                        slug=data.get("slug"),
                        description=data.get("description"),
                        icon=data.get("icon"),
                        is_free=data.get("is_free", True),
                        sort_order=data.get("sort_order", 0),
                        category_id=data.get("category_id"),
                    )

                    amenities.append(amenity)

                if amenities:
                    await RentalAmenity.bulk_create(amenities)

            return {
                "success": True,
                "message": f"{len(amenities)} amenities saved",
                # "data": [a.to_dict() for a in amenities],
            }

        except Exception as e:
            logger.exception(
                f"Amenity sync failed for rental {rental_id}", exc_info=e
            )
            return {
                "success": False,
                "message": "Failed to save amenities",
                "data": None,
            }

    async def save_pricing(
        self,
        rental_id: str,
        payload: PriceCreate,
        existing_rental: RentalComplex,
    ) -> dict:
        try:
            if not existing_rental:
                return {"success": False, "message": "Rental not found", "data": None}

            # Create or update pricing
            pricing_data = {
                "rent": payload.amount,
                "rent_frequency": payload.period.lower(),
                "currency": payload.currency,
                "deposit_amount": payload.deposit_amount or 0,
                "is_deposit_refundable": payload.is_refundable,
                "minimum_lease_months": payload.min_rent_period,
            }

            # If rental already has pricing, clear existing fees
            if existing_rental.pricing:
                await existing_rental.pricing.delete()

            pricing = await RentalPricing.create(**pricing_data)
            existing_rental.pricing = pricing
            await existing_rental.save(update_fields=["pricing_id"])

            # Save extra fees
            for index, fee in enumerate(payload.extra_fees or []):
                extra_fee = await RentalPricingExtraFees.create(
                    pricing=pricing,
                    code=fee.code,
                    name=fee.name,
                    amount=fee.amount,
                    description=fee.description,
                    currency=payload.currency,
                    is_included=fee.is_included,
                    sort_order=index,
                )

            return {"success": True, "message": "Pricing saved successfully", "data": pricing.id}

        except Exception as err:
            logger.exception("Failed to save pricing", exc_info=err)
            return {"success": False, "message": "Failed to save pricing", "data": None}

    async def save_rules(
        self,
        rental_id: str,
        payload: list[PropertyRuleCreate],
        existing_rental: RentalComplex,
    ) -> dict:
        try:
            if not existing_rental:
                return {
                    "success": False,
                    "message": "Rental not found",
                    "data": None,
                }

            # Remove existing rules (replace strategy)
            await RentalRules.filter(rental=existing_rental).delete()

            rules = [
                RentalRules(
                    rental=existing_rental,
                    title=rule.title,
                    description=rule.description,
                    is_mandatory=rule.is_mandatory if rule.is_mandatory is not None else True,
                )
                for rule in payload
            ]

            if rules:
                await RentalRules.bulk_create(rules)

            return {
                "success": True,
                "message": "Rules saved successfully",
                "data": None,
            }

        except Exception as err:
            logger.exception("Failed to save rules", exc_info=err)
            return {
                "success": False,
                "message": "Failed to save rules",
                "data": None,
            }

    async def update_status(self, rental_id: str, status: RentalStatus) -> Optional[RentalComplex]:
        """Update rental status."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return None
        
        rental.status = status
        rental.updated_at = datetime.now()
        
        # Update availability based on status
        if status in [RentalStatus.VACANT, RentalStatus.RENTED]:
            rental.is_available = False
        elif status == RentalStatus.RESERVED:
            rental.is_available = False
        else:
            rental.is_available = True
        
        await rental.save()
        return rental

    async def toggle_availability(self, rental_id: str) -> Optional[RentalComplex]:
        """Toggle rental availability."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return None
        
        rental.is_available = not rental.is_available
        rental.updated_at = datetime.now()
        await rental.save()
        return rental

    async def toggle_featured(self, rental_id: str) -> Optional[RentalComplex]:
        """Toggle featured status."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return None
        
        rental.is_featured = not rental.is_featured
        rental.updated_at = datetime.now()
        await rental.save()
        return rental

    # Manager Management
    async def add_manager(self, rental_id: str, user_id: str) -> bool:
        """Add a manager to rental."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return False
        
        # Check if user is already a manager
        is_manager = await rental.managers.filter(id=user_id).exists()
        if is_manager:
            return True
        
        # Add manager
        await rental.managers.add(user_id)
        return True

    async def remove_manager(self, rental_id: str, user_id: str) -> bool:
        """Remove manager from rental."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return False
        
        # Check if user is a manager
        is_manager = await rental.managers.filter(id=user_id).exists()
        if not is_manager:
            return True
        
        # Remove manager (can't remove owner)
        if rental.publisher_id != user_id:
            await rental.managers.remove(user_id)
            return True
        return False

    async def get_managers(self, rental_id: str) -> List[User]:
        """Get all managers for a rental."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return []
        
        return await rental.managers.all()

    # Delete & Archive Operations
    async def soft_delete(self, rental_id: str) -> bool:
        """Soft delete a rental (mark as deleted)."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return False
        
        rental.is_deleted = True
        rental.deleted_at = datetime.now()
        await rental.save()
        return True

    async def hard_delete(self, rental_id: str) -> bool:
        """Permanently delete a rental."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return False
        
        await rental.delete()
        return True

    async def restore(self, rental_id: str) -> bool:
        """Restore a soft-deleted rental."""
        rental = await self.get_by_id(rental_id)
        if not rental or not rental.is_deleted:
            return False
        
        rental.is_deleted = False
        rental.deleted_at = None
        rental.updated_at = datetime.now()
        await rental.save()
        return True

    # Search & Filter Operations
    async def search(self, query: str, limit: int = 20, offset: int = 0) -> List[RentalComplex]:
        """Search rentals by title, description, or address."""
        search_query = Q(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(city__icontains=query) |
            Q(state__icontains=query)
        )
        
        return await self.model.filter(
            search_query,
            is_available=True,
            is_deleted=False
        ).limit(limit).offset(offset).all()


    async def filter_rentals(
        self,
        public_id: Optional[str] = None,        
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        lat: Optional[Decimal] = None,
        long: Optional[Decimal] = None,
        radius: Optional[float] = 10,
        deposit: Optional[float] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        amenities: Optional[List[str]] = None,
        is_featured: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        
        query = self.model.filter(is_available=True, is_deleted=False)
        
        if public_id:            
            query = query.filter(public_id=public_id)
                    
        if category:            
            category_enum = PropertyCategory[category] 
            query = query.filter(category=category_enum.value)
        
        if min_price is not None:
            query = query.filter(price__gte=min_price)
        
        if max_price is not None:
            query = query.filter(price__lte=max_price)
        
        if bedrooms is not None:
            query = query.filter(bedrooms=bedrooms)
        
        if bathrooms is not None:
            query = query.filter(bathrooms=bathrooms)
        
        if city:
            query = query.filter(city__iexact=city)
        
        if state:
            query = query.filter(state__iexact=state)
        
        if is_featured is not None:
            query = query.filter(is_featured=is_featured)
        
        if is_verified is not None:
            query = query.filter(is_verified=is_verified)
        
        if status:
            query = query.filter(status=status)
        
        if amenities:
            for amenity in amenities:
                query = query.filter(amenities__name__iexact=amenity)
        
        if lat is not None and long is not None:
            query = query.filter(
                latitude__gte=lat - Decimal(radius/111.32),
                latitude__lte=lat + Decimal(radius/111.32),
                longitude__gte=long - Decimal(radius/(111.32 * abs(cos(float(lat))))),
                longitude__lte=long + Decimal(radius/(111.32 * abs(cos(float(lat)))))
            )
        
        if sort_by:
            sort_map = {
                'price_asc': 'price',
                'price_desc': '-price',
                'newest': '-created_at',
                'oldest': 'created_at',
                'featured': '-is_featured',
                'bedrooms_asc': 'bedrooms',
                'bedrooms_desc': '-bedrooms'
            }
            if sort_by in sort_map:
                query = query.order_by(sort_map[sort_by])
            else:
                query = query.order_by('-is_featured', '-created_at')
        else:
            query = query.order_by('-is_featured', '-created_at')
        
        query = query.limit(limit).offset(offset)
        
        rentals = await query.prefetch_related('rules', 'amenities', 'pricing__fees', 'gallery','publisher','managers')
        
        data = []
        for rental in rentals:
            data.append(self._rental_to_dict(rental))
        return data

    async def list_public_rentals(self, limit: int = 20, offset: int = 0):
        """Get public rentals that are available and not deleted."""
        
        try:
            # Use prefetch_related to fetch everything in one query
            rentals = await self.model.filter(
                is_available=True,
                is_deleted=False
            ).prefetch_related('rules', 'amenities', 'pricing__fees', 'gallery','publisher','managers') \
            .limit(limit).offset(offset)
            
            print(f"Found {len(rentals)} rentals")
            data = []
            for rental in rentals:
                data.append(self._rental_to_dict(rental))
            return data
            
        except Exception as e:
            print(f"Error in list_public_rentals: {e}")
            # Return empty list on error, or handle as needed
            return []
        

    async def get_nearby_rentals(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10,
        limit: int = 20
    ) -> List[RentalComplex]:
        """Get rentals within a certain radius (simplified)."""
        # This is a simplified version. In production, you'd use PostGIS or similar
        return await self.model.filter(
            is_available=True,
            is_deleted=False,
            latitude__isnull=False,
            longitude__isnull=False
        ).limit(limit).all()

    async def get_featured_rentals(self, limit: int = 10) -> List[RentalComplex]:
        """Get featured rentals."""
        return await self.model.filter(
            is_featured=True,
            is_available=True,
            is_deleted=False
        ).limit(limit).all()

    async def get_verified_rentals(self, limit: int = 20) -> List[RentalComplex]:
        """Get verified rentals."""
        return await self.model.filter(
            is_verified=True,
            is_available=True,
            is_deleted=False
        ).limit(limit).all()

    # Statistics & Analytics
    async def get_user_rental_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rental statistics for a user."""
        total = await self.model.filter(publisher_id=user_id, is_deleted=False).count()
        available = await self.model.filter(publisher_id=user_id, is_available=True, is_deleted=False).count()
        rented = await self.model.filter(publisher_id=user_id, status=RentalStatus.RENTED, is_deleted=False).count()
        featured = await self.model.filter(publisher_id=user_id, is_featured=True, is_deleted=False).count()
        verified = await self.model.filter(publisher_id=user_id, is_verified=True, is_deleted=False).count()
        
        return {
            "total_rentals": total,
            "available_rentals": available,
            "rented_rentals": rented,
            "featured_rentals": featured,
            "verified_rentals": verified
        }

    async def get_rental_count_by_category(self) -> Dict[str, int]:
        """Get count of rentals by category."""
        categories = {}
        for category in PropertyCategory:
            count = await self.model.filter(
                category=category,
                is_available=True,
                is_deleted=False
            ).count()
            categories[category.value] = count
        return categories

    # Validation & Verification
    async def verify_rental(self, rental_id: str, admin_user_id: str) -> Optional[RentalComplex]:
        """Mark rental as verified by admin."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return None
        
        rental.is_verified = True
        rental.verified_by_id = admin_user_id
        rental.verified_at = datetime.now()
        await rental.save()
        return rental

    async def unverify_rental(self, rental_id: str) -> Optional[RentalComplex]:
        """Remove verification from rental."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return None
        
        rental.is_verified = False
        rental.verified_by_id = None
        rental.verified_at = None
        await rental.save()
        return rental

    async def reject_rental(self, rental_id: str, reason: str) -> Optional[RentalComplex]:
        """Reject rental with a reason."""
        rental = await self.get_by_id(rental_id)
        if not rental:
            return None
        
        rental.is_verified = False
        rental.rejection_reason = reason
        rental.verified_at = None
        rental.verified_by_id = None
        await rental.save()
        return rental

    # Bulk Operations
    async def bulk_update_status(
        self,
        rental_ids: List[str],
        status: RentalStatus
    ) -> int:
        """Update status for multiple rentals."""
        updated = await self.model.filter(
            id__in=rental_ids
        ).update(
            status=status,
            updated_at=datetime.now()
        )
        return updated

    async def bulk_toggle_availability(
        self,
        rental_ids: List[str],
        make_available: bool
    ) -> int:
        """Toggle availability for multiple rentals."""
        updated = await self.model.filter(
            id__in=rental_ids
        ).update(
            is_available=make_available,
            updated_at=datetime.now()
        )
        return updated
    
    
    
    def _rental_to_dict(self, rental):
        site_info = settings.SITE
        category_enum = PropertyCategory(rental.category)

        return {
            "id": rental.id,
            "public_id": rental.public_id,
            "title": rental.title,
            "slug": rental.slug,
            "status":rental.status,
            "theme_color":rental.theme_color,
            "category": category_enum.name,
            "category_id": rental.category,
            "description": rental.description,
            "profile_picture": rental.profile_picture if 'https' in  rental.profile_picture else f"{site_info.FILE_READ_API}/{rental.profile_picture}",
            "bedrooms": rental.bedrooms,
            "bathrooms": float(rental.bathrooms),
            "city": rental.city,
            "state": rental.state,
            "latitude": rental.latitude,
            "longitude": rental.longitude,
            "address": rental.address,
            "price": float(rental.price) if rental.price else None,
            "is_available": rental.is_available,
            "status": rental.status.value,
            "is_featured": rental.is_featured,
            "is_verified": rental.is_verified,
            "created_at": rental.created_at.isoformat() if rental.created_at else None,
            "pricing": (
                {
                    "base_price": rental.pricing,
                    "extra_fees": [
                        {
                            "id": fee.id,
                            "name": fee.name,
                            "amount": float(fee.amount) if fee.amount is not None else None,
                            "is_included": fee.is_included,
                            "sort_order": fee.sort_order,
                            "currency": fee.currency,
                        }
                        for fee in (rental.pricing.fees or [])
                    ],
                }
                if rental.pricing
                else {
                    "base_price": None,
                    "extra_fees": [],
                }
            ),

            "amenities": [
                {
                    "id": amenity.id,
                    "name": amenity.name,
                    "slug": amenity.slug,
                    "description": amenity.description,
                    "sort_order": amenity.sort_order,
                    "is_featured": amenity.is_featured,
                    "icon": amenity.icon
                } for amenity in rental.amenities
            ],
            "gallery": [
                {
                    "url": image.image_url if 'https' in image.image_url else f"{site_info.FILE_READ_API}/{image.image_url}",
                    "caption": image.title or image.description,
                    "file_type": image.file_type,
                    "mime_type": image.mime_type,
                    "is_primary": image.is_primary
                } for image in rental.gallery
            ],
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "description": rule.description,
                    "is_mandatory": rule.is_mandatory
                } for rule in rental.rules
            ],
              "publisher":{
                         "public_id":rental.publisher.public_id,
                         "display_name":rental.publisher.display_name,
                         "profile_picture":rental.publisher.profile_picture,
            },
            "managers":{
                         "public_id":rental.managers.public_id,
                         "display_name":rental.managers.display_name,
                         "profile_picture":rental.managers.profile_picture,
                         }if rental.managers else None,
          
        }



    def _full_rental_to_dict(self, rental):
        site_info = settings.SITE
        category_enum = PropertyCategory(rental.category)

        return {
            "id": rental.id,
            "public_id": rental.public_id,
            "title": rental.title,
            "slug": rental.slug,
            "status":rental.status,
            "theme_color":rental.theme_color,
            "category": category_enum.name,
            "category_id": rental.category,
            "description": rental.description,
            "profile_picture": rental.profile_picture if 'https' in  rental.profile_picture else f"{site_info.FILE_READ_API}/{rental.profile_picture}",
            "bedrooms": rental.bedrooms,
            "bathrooms": float(rental.bathrooms),
            "city": rental.city,
            "state": rental.state,
            "latitude": rental.latitude,
            "longitude": rental.longitude,
            "address": rental.address,
            "price": float(rental.price) if rental.price else None,
            "is_available": rental.is_available,
            "status": rental.status.value,
            "is_featured": rental.is_featured,
            "is_verified": rental.is_verified,
            "created_at": rental.created_at.isoformat() if rental.created_at else None,
            "pricing": rental.pricing,
            "amenities": [
                {
                    "id": amenity.id,
                    "name": amenity.name,
                    "slug": amenity.slug,
                    "description": amenity.description,
                    "sort_order": amenity.sort_order,
                    "is_featured": amenity.is_featured,
                    "icon": amenity.icon
                } for amenity in rental.amenities
            ],
            "gallery": [
                {
                    "url": image.image_url if 'https' in image.image_url else f"{site_info.FILE_READ_API}/{image.image_url}",
                    "caption": image.title or image.description,
                    "file_type": image.file_type,
                    "mime_type": image.mime_type,
                    "is_primary": image.is_primary
                } for image in rental.gallery
            ],
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "description": rule.description,
                    "is_mandatory": rule.is_mandatory
                } for rule in rental.rules
            ]
        }




# Factory function for dependency injection
def get_rental_repo() -> RentalRepository:
    return RentalRepository()