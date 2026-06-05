from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status, Request
from typing import List, Optional, Dict, Any
import traceback

from services.apartment import ApartmentService
from repositories.apartment import ApartmentRepository
from schemas.request.apartment import (
    ApartmentCreate, ApartmentUpdate, ApartmentImageUpload,
    ApartmentPublish, ApartmentFeatureUpdate, BulkApartmentUpdate
)
from schemas.response.apartment import (
    ApartmentDetail, ApartmentSummary, ApartmentList,
    ApartmentStats, ApartmentAnalytics, ApartmentImage
)
from core.security import (
    get_current_user,
    get_current_admin,
    require_permission_dependency as require_permission
)
from models.apartment import ApartmentStatus
from core.limiter import limiter
from core.logger import setup_logger
from core.settings import settings

logger = setup_logger(__name__)

apartment_router = APIRouter(
    prefix="/apartments",
    tags=["Apartments"]
)


# Dependency injections
def get_apartment_repo():
    return ApartmentRepository()

def get_apartment_service(repo: ApartmentRepository = Depends(get_apartment_repo)):
    return ApartmentService(repo)


# Permission dependencies
require_apartment_view = require_permission("property_management", "view")
require_apartment_create = require_permission("property_management", "create")
require_apartment_edit = require_permission("property_management", "edit")
require_apartment_delete = require_permission("property_management", "delete")
require_apartment_approve = require_permission("property_management", "approve")
require_apartment_feature = require_permission("property_management", "feature")


# Request logging middleware
async def log_apartment_request(request: Request, operation: str, **kwargs):
    logger.info(f"Apartment {operation}", extra={
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
        **kwargs
    })


@apartment_router.get("/stats", response_model=ApartmentStats)
@limiter.limit(settings.APARTMENT_STATS_RATE_LIMIT)
async def get_apartment_stats(
    request: Request,
    service: ApartmentService = Depends(get_apartment_service),
    admin: Any = Depends(get_current_admin)
):
    await log_apartment_request(request, "get_stats", admin_id=str(admin.id))
    
    try:
        repo_stats = await service.repo.get_stats()
        
        # Add additional stats
        apartments, _ = await service.get_apartments_with_filters(
            filters={"status": ApartmentStatus.ACTIVE},
            limit=1000
        )
        
        # Calculate type distribution
        type_stats = {}
        for apt in apartments:
            apt_type = apt.type or "Unknown"
            type_stats[apt_type] = type_stats.get(apt_type, 0) + 1
        
        # Calculate price ranges
        price_ranges = {
            "0-500": 0,
            "501-1000": 0,
            "1001-2000": 0,
            "2001-5000": 0,
            "5000+": 0
        }
        
        for apt in apartments:
            price = apt.price or 0
            if price <= 500:
                price_ranges["0-500"] += 1
            elif price <= 1000:
                price_ranges["501-1000"] += 1
            elif price <= 2000:
                price_ranges["1001-2000"] += 1
            elif price <= 5000:
                price_ranges["2001-5000"] += 1
            else:
                price_ranges["5000+"] += 1
        
        # Calculate average price
        active_prices = [apt.price for apt in apartments if apt.price]
        avg_price = round(sum(active_prices) / len(active_prices), 2) if active_prices else 0
        
        stats = ApartmentStats(
            total_apartments=repo_stats["total"],
            active_apartments=repo_stats["active"],
            pending_approval=repo_stats["pending"],
            rented_apartments=0,  # Would come from rental service
            featured_apartments=repo_stats["featured"],
            by_type=type_stats,
            by_price_range=price_ranges,
            avg_price=avg_price,
            recent_listings=[]
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get apartment stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve apartment statistics"
        )


@apartment_router.post("/", response_model=ApartmentDetail, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.APARTMENT_CREATE_RATE_LIMIT)
async def create_apartment(
    request: Request,
    apartment_data: ApartmentCreate,
    service: ApartmentService = Depends(get_apartment_service),
    user: Any = Depends(get_current_user)
):
    await log_apartment_request(
        request, "create", 
        user_id=str(user.id),
        title=apartment_data.title
    )
    
    try:
        # Check user's apartment limit
        user_apartments = await service.repo.get_by_owner(str(user.id))
        if len(user_apartments) >= settings.MAX_APARTMENTS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum apartment limit reached ({settings.MAX_APARTMENTS_PER_USER})"
            )
        
        apartment = await service.create_apartment(apartment_data, str(user.id))
        return await service.repo.to_schema(apartment)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create apartment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create apartment"
        )


@apartment_router.get("/", response_model=ApartmentList)
@limiter.limit(settings.APARTMENT_LIST_RATE_LIMIT)
async def list_apartments(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    bedrooms: Optional[int] = Query(None, ge=0),
    city: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    service: ApartmentService = Depends(get_apartment_service),
    user: Any = Depends(get_current_user)
):
    await log_apartment_request(
        request, "list",
        user_id=str(user.id),
        skip=skip,
        limit=limit
    )
    
    try:
        filters = {
            "status": status,
            "type": type,
            "min_price": min_price,
            "max_price": max_price,
            "bedrooms": bedrooms,
            "city": city,
            "featured": featured
        }
        
        # Non-adins can only see active apartments
        if not hasattr(user, 'is_admin') or not user.is_admin:
            filters["status"] = ApartmentStatus.ACTIVE
        
        apartments, total = await service.get_apartments_with_filters(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        apartment_summaries = [
            await service.repo.to_summary_schema(apartment)
            for apartment in apartments
        ]
        
        return ApartmentList(
            apartments=apartment_summaries,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            limit=limit,
            has_more=(skip + limit) < total
        )
        
    except Exception as e:
        logger.error(f"Failed to list apartments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve apartments"
        )


@apartment_router.get("/{apartment_id}", response_model=ApartmentDetail)
@limiter.limit(settings.APARTMENT_DETAIL_RATE_LIMIT)
async def get_apartment(
    request: Request,
    apartment_id: str = Path(...),
    service: ApartmentService = Depends(get_apartment_service),
    user: Any = Depends(get_current_user)
):
    await log_apartment_request(request, "get_detail", apartment_id=apartment_id, user_id=str(user.id))
    
    try:
        apartment = await service.repo.get_by_id(apartment_id)
        if not apartment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Apartment not found"
            )
        
        # Check permissions
        is_owner = str(apartment.owner_id) == str(user.id)
        is_admin = hasattr(user, 'is_admin') and user.is_admin
        
        if apartment.status != ApartmentStatus.ACTIVE and not is_owner and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apartment is not available for viewing"
            )
        
        return await service.repo.to_schema(apartment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get apartment {apartment_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve apartment"
        )


@apartment_router.put("/{apartment_id}", response_model=ApartmentDetail)
@limiter.limit(settings.APARTMENT_UPDATE_RATE_LIMIT)
async def update_apartment(
    request: Request,
    apartment_id: str = Path(...),
    update_data: ApartmentUpdate = Body(...),
    service: ApartmentService = Depends(get_apartment_service),
    user: Any = Depends(get_current_user)
):
    await log_apartment_request(
        request, "update",
        apartment_id=apartment_id,
        user_id=str(user.id)
    )
    
    try:
        is_admin = hasattr(user, 'is_admin') and user.is_admin
        
        apartment = await service.update_apartment(
            apartment_id=apartment_id,
            data=update_data,
            user_id=str(user.id),
            is_admin=is_admin
        )
        
        return await service.repo.to_schema(apartment)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update apartment {apartment_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update apartment"
        )


@apartment_router.delete("/{apartment_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.APARTMENT_DELETE_RATE_LIMIT)
async def delete_apartment(
    request: Request,
    apartment_id: str = Path(...),
    service: ApartmentService = Depends(get_apartment_service),
    user: Any = Depends(get_current_user)
):
    await log_apartment_request(
        request, "delete",
        apartment_id=apartment_id,
        user_id=str(user.id)
    )
    
    try:
        is_admin = hasattr(user, 'is_admin') and user.is_admin
        
        await service.delete_apartment(
            apartment_id=apartment_id,
            user_id=str(user.id),
            is_admin=is_admin
        )
        
        return None
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete apartment {apartment_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete apartment"
        )


@apartment_router.post("/{apartment_id}/publish", response_model=ApartmentDetail)
@limiter.limit(settings.APARTMENT_PUBLISH_RATE_LIMIT)
async def publish_apartment(
    request: Request,
    apartment_id: str = Path(...),
    publish_data: ApartmentPublish = Body(...),
    service: ApartmentService = Depends(get_apartment_service),
    user: Any = Depends(get_current_user)
):
    await log_apartment_request(
        request, "publish",
        apartment_id=apartment_id,
        user_id=str(user.id),
        publish=publish_data.publish
    )
    
    try:
        apartment = await service.publish_apartment(
            apartment_id=apartment_id,
            user_id=str(user.id),
            publish=publish_data.publish
        )
        
        return await service.repo.to_schema(apartment)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to publish apartment {apartment_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish apartment"
        )


@apartment_router.post("/{apartment_id}/feature", response_model=ApartmentDetail)
@limiter.limit(settings.APARTMENT_FEATURE_RATE_LIMIT)
async def feature_apartment(
    request: Request,
    apartment_id: str = Path(...),
    feature_data: ApartmentFeatureUpdate = Body(...),
    service: ApartmentService = Depends(get_apartment_service),
    admin: Any = Depends(require_apartment_feature)
):
    await log_apartment_request(
        request, "feature",
        apartment_id=apartment_id,
        admin_id=str(admin.id),
        featured=feature_data.featured
    )
    
    try:
        apartment = await service.feature_apartment(
            apartment_id=apartment_id,
            featured=feature_data.featured,
            priority=feature_data.priority
        )
        
        return await service.repo.to_schema(apartment)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to feature apartment {apartment_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to feature apartment"
        )


@apartment_router.get("/my-apartments", response_model=List[ApartmentSummary])
@limiter.limit(settings.APARTMENT_MY_LIST_RATE_LIMIT)
async def get_my_apartments(
    request: Request,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ApartmentService = Depends(get_apartment_service),
    user: Any = Depends(get_current_user)
):
    await log_apartment_request(
        request, "list_my_apartments",
        user_id=str(user.id),
        status=status
    )
    
    try:
        apartments = await service.repo.get_by_owner(
            owner_id=str(user.id),
            status=status
        )
        
        # Apply pagination
        paginated_apartments = apartments[skip:skip + limit]
        
        return [
            await service.repo.to_summary_schema(apartment)
            for apartment in paginated_apartments
        ]
        
    except Exception as e:
        logger.error(f"Failed to get user apartments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve your apartments"
        )


@apartment_router.post("/bulk-update", response_model=Dict[str, Any])
@limiter.limit(settings.APARTMENT_BULK_RATE_LIMIT)
async def bulk_update_apartments(
    request: Request,
    bulk_data: BulkApartmentUpdate = Body(...),
    service: ApartmentService = Depends(get_apartment_service),
    admin: Any = Depends(require_apartment_edit)
):
    await log_apartment_request(
        request, "bulk_update",
        admin_id=str(admin.id),
        apartment_count=len(bulk_data.apartment_ids)
    )
    
    try:
        results = {"success": [], "failed": []}
        
        for apartment_id in bulk_data.apartment_ids:
            try:
                apartment = await service.update_apartment(
                    apartment_id=apartment_id,
                    data=ApartmentUpdate(**bulk_data.update_data),
                    user_id=str(admin.id),
                    is_admin=True
                )
                results["success"].append(apartment_id)
                
            except Exception as e:
                results["failed"].append({
                    "apartment_id": apartment_id,
                    "error": str(e)
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to bulk update apartments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk update apartments"
        )