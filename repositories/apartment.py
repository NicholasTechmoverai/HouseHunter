from typing import List, Optional, Dict, Any
from tortoise.expressions import Q
from tortoise.expressions import Subquery

from models.apartment import Apartment, ApartmentStatus, ApartmentType
from schemas.response.apartment import ApartmentDetail, ApartmentSummary, OwnerInfo, ApartmentImage
from .base_repository import BaseRepository
from core.cache import cache_manager


class ApartmentRepository(BaseRepository[Apartment, ApartmentDetail]):
    
    def __init__(self):
        super().__init__(Apartment, ApartmentDetail)
    
    async def get_by_id(self, id: str, include_deleted: bool = False) -> Optional[Apartment]:
        query = self.model.filter(id=id)
        if not include_deleted:
            query = query.filter(is_deleted=False)
        return await query.first()
    
    async def get_by_owner(self, owner_id: str, status: Optional[str] = None) -> List[Apartment]:
        query = self.model.filter(owner_id=owner_id, is_deleted=False)
        if status:
            query = query.filter(status=status)
        return await query.all()
    
    async def search_apartments(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bedrooms: Optional[int] = None,
        city: Optional[str] = None,
        featured: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Apartment], int]:
        query = self.model.filter(is_deleted=False)
        
        # Apply filters
        if status:
            query = query.filter(status=status)
        if type:
            query = query.filter(type=type)
        if min_price is not None:
            query = query.filter(price__gte=min_price)
        if max_price is not None:
            query = query.filter(price__lte=max_price)
        if bedrooms:
            query = query.filter(bedrooms=bedrooms)
        if city:
            query = query.filter(city__icontains=city)
        if featured is not None:
            query = query.filter(is_featured=featured)
        
        # Get total count
        total = await query.count()
        
        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(f"-{sort_by}")
        else:
            query = query.order_by(sort_by)
        
        # Apply pagination
        apartments = await query.offset(skip).limit(limit).prefetch_related(
            "owner"
        ).all()
        
        return apartments, total
    
    async def text_search(
        self,
        query_text: str,
        field: str = "all",
        skip: int = 0,
        limit: int = 50
    ) -> List[Apartment]:
        query = self.model.filter(is_deleted=False, status=ApartmentStatus.ACTIVE)
        
        if field == "title":
            query = query.filter(title__icontains=query_text)
        elif field == "description":
            query = query.filter(description__icontains=query_text)
        elif field == "address":
            query = query.filter(address__icontains=query_text)
        elif field == "city":
            query = query.filter(city__icontains=query_text)
        else:
            query = query.filter(
                Q(title__icontains=query_text) |
                Q(description__icontains=query_text) |
                Q(address__icontains=query_text) |
                Q(city__icontains=query_text)
            )
        
        return await query.offset(skip).limit(limit).prefetch_related("owner").all()
    
    async def update_apartment(self, apartment_id: str, data: Dict[str, Any]) -> Apartment:
        apartment = await self.get_by_id(apartment_id)
        if not apartment:
            raise ValueError("Apartment not found")
        
        return await self.update(apartment, data)
    
    async def add_images(self, apartment_id: str, images: List[Dict[str, str]]) -> List[Dict[str, str]]:
        apartment = await self.get_by_id(apartment_id)
        if not apartment:
            raise ValueError("Apartment not found")
        
        current_images = apartment.images or []
        current_images.extend(images)
        
        await self.update(apartment, {"images": current_images})
        return images
    
    async def validate_publish_requirements(self, apartment: Apartment) -> List[str]:
        errors = []
        
        if not apartment.title:
            errors.append("Title is required")
        if not apartment.description:
            errors.append("Description is required")
        if not apartment.price or apartment.price <= 0:
            errors.append("Valid price is required")
        if not apartment.address:
            errors.append("Address is required")
        if not apartment.city:
            errors.append("City is required")
        if not hasattr(apartment, 'images') or not apartment.images:
            errors.append("At least one image is required")
        elif len(apartment.images) < 3:
            errors.append("At least 3 images are required")
        
        return errors
    
    async def get_analytics(self, apartment_id: str, period: str) -> Dict[str, Any]:
        apartment = await self.get_by_id(apartment_id)
        if not apartment:
            raise ValueError("Apartment not found")
        
        # This would integrate with your analytics service
        # For now, return mock data
        return {
            "apartment_id": apartment_id,
            "views": 150,
            "contacts": 25,
            "favorites": 12,
            "period": period,
            "trend": "increasing"
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        cache_key = "apartment_stats"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached
        
        stats = {
            "total": await self.model.filter(is_deleted=False).count(),
            "active": await self.model.filter(
                is_deleted=False, 
                status=ApartmentStatus.ACTIVE
            ).count(),
            "pending": await self.model.filter(
                is_deleted=False,
                status=ApartmentStatus.PENDING
            ).count(),
            "featured": await self.model.filter(
                is_deleted=False,
                is_featured=True,
                status=ApartmentStatus.ACTIVE
            ).count(),
        }
        
        await cache_manager.set(cache_key, stats, expire=300)
        return stats
    
    async def to_summary_schema(self, apartment: Apartment) -> ApartmentSummary:
        return ApartmentSummary(
            id=str(apartment.id),
            title=apartment.title,
            description=apartment.description[:150] + "..." if apartment.description and len(apartment.description) > 150 else apartment.description,
            price=apartment.price,
            type=apartment.type,
            bedrooms=apartment.bedrooms,
            bathrooms=apartment.bathrooms,
            area=apartment.area,
            city=apartment.city,
            status=apartment.status,
            is_featured=apartment.is_featured,
            thumbnail=apartment.images[0]["url"] if apartment.images and len(apartment.images) > 0 else None,
            created_at=apartment.created_at,
            updated_at=apartment.updated_at
        )

    async def to_schema(self, apartment: Apartment) -> ApartmentDetail:
        owner = await apartment.owner
        owner_info = OwnerInfo(
            id=str(owner.id),
            username=owner.username,
            display_name=getattr(owner, "display_name", f"{owner.first_name} {owner.last_name}".strip()),
            profile_pic=getattr(owner, "profile_picture", None),
            verified=getattr(owner, "is_verified", False)
        )
        
        images = []
        for img in (apartment.images or []):
            images.append(ApartmentImage(
                url=img.get("url"),
                caption=img.get("caption"),
                is_primary=img.get("is_primary", False),
                uploaded_at=img.get("uploaded_at") or apartment.created_at
            ))
            
        return ApartmentDetail(
            id=str(apartment.id),
            title=apartment.title,
            description=apartment.description,
            price=float(apartment.price),
            type=apartment.type,
            bedrooms=apartment.bedrooms,
            bathrooms=apartment.bathrooms,
            area=float(apartment.area) if apartment.area else None,
            address=apartment.address,
            city=apartment.city,
            amenities=apartment.amenities or [],
            latitude=apartment.latitude,
            longitude=apartment.longitude,
            status=apartment.status,
            is_featured=apartment.is_featured,
            feature_priority=apartment.feature_priority,
            images=images,
            owner=owner_info,
            view_count=apartment.view_count,
            favorite_count=apartment.favorite_count,
            created_at=apartment.created_at,
            updated_at=apartment.updated_at,
            published_at=apartment.published_at,
            approved_by=str(apartment.approved_by_id) if apartment.approved_by_id else None,
            approved_at=apartment.approved_at
        )