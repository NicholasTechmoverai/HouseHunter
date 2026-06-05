from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.apartment import ApartmentRepository
from schemas.request.apartment import ApartmentCreate, ApartmentUpdate
from models.apartment import Apartment, ApartmentStatus
from core.cache import cache_manager


class ApartmentService:
    
    def __init__(self, repo: ApartmentRepository):
        self.repo = repo
    
    async def create_apartment(self, data: ApartmentCreate, owner_id: str) -> Apartment:
        apartment_data = data.dict()
        apartment_data["owner_id"] = owner_id
        apartment_data["created_by_id"] = owner_id
        
        # Set initial status
        apartment_data["status"] = ApartmentStatus.PENDING
        
        apartment = await self.repo.create(apartment_data)
        
        # Clear relevant caches
        await self._clear_apartment_caches()
        
        return apartment
    
    async def update_apartment(self, apartment_id: str, data: ApartmentUpdate, user_id: str, is_admin: bool = False) -> Apartment:
        apartment = await self.repo.get_by_id(apartment_id)
        if not apartment:
            raise ValueError("Apartment not found")
        
        # Check permissions
        if not is_admin and str(apartment.owner_id) != user_id:
            raise PermissionError("Not authorized to update this apartment")
        
        update_data = data.dict(exclude_none=True)
        
        # If admin is changing status, track it
        if is_admin and "status" in update_data:
            update_data["approved_by"] = user_id
            update_data["approved_at"] = datetime.now(timezone.utc)
        
        updated_apartment = await self.repo.update_apartment(apartment_id, update_data)
        
        # Clear caches
        await self._clear_apartment_caches(apartment_id)
        
        return updated_apartment
    
    async def delete_apartment(self, apartment_id: str, user_id: str, is_admin: bool = False) -> bool:
        apartment = await self.repo.get_by_id(apartment_id)
        if not apartment:
            raise ValueError("Apartment not found")
        
        # Check permissions
        if not is_admin and str(apartment.owner_id) != user_id:
            raise PermissionError("Not authorized to delete this apartment")
        
        # Soft delete
        await self.repo.update(apartment, {"is_deleted": True})
        
        # Clear caches
        await self._clear_apartment_caches(apartment_id)
        
        return True
    
    async def publish_apartment(self, apartment_id: str, user_id: str, publish: bool = True) -> Apartment:
        apartment = await self.repo.get_by_id(apartment_id)
        if not apartment:
            raise ValueError("Apartment not found")
        
        if str(apartment.owner_id) != user_id:
            raise PermissionError("Not authorized to publish this apartment")
        
        validation_errors = await self.repo.validate_publish_requirements(apartment)
        if validation_errors:
            raise ValueError(f"Cannot publish apartment: {', '.join(validation_errors)}")
        
        update_data = {
            "status": ApartmentStatus.ACTIVE if publish else ApartmentStatus.DRAFT
        }
        
        if publish:
            update_data["published_at"] = datetime.now(timezone.utc)
        
        updated_apartment = await self.repo.update_apartment(apartment_id, update_data)
        
        await self._clear_apartment_caches(apartment_id)
        
        return updated_apartment
    
    async def feature_apartment(self, apartment_id: str, featured: bool, priority: Optional[int] = None) -> Apartment:
        apartment = await self.repo.get_by_id(apartment_id)
        if not apartment:
            raise ValueError("Apartment not found")
        
        if apartment.status != ApartmentStatus.ACTIVE:
            raise ValueError("Only active apartments can be featured")
        
        update_data = {"is_featured": featured}
        if priority is not None:
            update_data["feature_priority"] = priority
        
        updated_apartment = await self.repo.update_apartment(apartment_id, update_data)
        
        await self._clear_apartment_caches(apartment_id)
        
        return updated_apartment
    
    async def get_apartments_with_filters(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[Apartment], int]:
        
        if not filters:
            filters = {}
        
        return await self.repo.search_apartments(
            skip=skip,
            limit=limit,
            status=filters.get("status"),
            type=filters.get("type"),
            min_price=filters.get("min_price"),
            max_price=filters.get("max_price"),
            bedrooms=filters.get("bedrooms"),
            city=filters.get("city"),
            featured=filters.get("featured"),
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    async def _clear_apartment_caches(self, apartment_id: Optional[str] = None):
        """Clear relevant caches when apartment data changes"""
        cache_patterns = ["apartment_stats:*", "apartment_list:*"]
        
        if apartment_id:
            cache_patterns.append(f"apartment_detail:{apartment_id}")
        
        for pattern in cache_patterns:
            await cache_manager.delete_pattern(pattern)