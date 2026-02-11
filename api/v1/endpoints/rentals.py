from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Depends, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from core.limiter import limiter
from schemas.request.rental import (
    HeadInfoCreate, 
    HeadInfoRecord,
    HeadInfoResponse,
    LocationCreate, 
    PriceCreate, 
    AmenityCreate, 
    PropertyRuleCreate,
    RentalCreate,
    FileUploadResponse,
    SearchRequest,
    RentalFilter
)
import json
from schemas.response.rental import (
    RentalResponse,
    ListRentalResponse
)
from repositories.rentals import get_rental_repo
from core.logger import setup_logger
from core.security import get_current_user,get_optional_current_user
from models.user import User
from tortoise.exceptions import ValidationError, IntegrityError, DoesNotExist
from utils.image_save import save_files_batch,save_uploaded_file,save_files_batch_sync
from services.search_service import get_query_parser
from decimal import Decimal

logger = setup_logger(__name__)

rental_router = APIRouter(
    prefix="/rental",
    tags=["Rental"]
)

@rental_router.post("/{rental_id}/head-info")
@limiter.limit("100/minute")
async def update_head_info(
    request: Request,
    rental_id: str,
    data: HeadInfoRecord,
    current_user: User = Depends(get_current_user)
) -> HeadInfoResponse:
    try:
        rental_repo = get_rental_repo()
        
        rental = await rental_repo.get_by_id_with_owner_check(
            rental_id=str(rental_id),
            user_id=current_user.id
        )
        
        updated_rental = await rental_repo.save_head_info(
            user_id=current_user.id,
            rental_id=str(rental_id),
            payload=data.data,
            existing_rental=rental
        )
        updated_rental = await updated_rental.to_dict()
        
        # print("RENTAL",updated_rental)

        
        logger.info(
            f"Updated head info for rental {rental_id}",
            extra={
                "rental_id": str(rental_id),
            }
        )
        
        return HeadInfoResponse(
            data=updated_rental,
            message="Head information updated successfully",
            success=True
        )
        
    except DoesNotExist:
        updated_rental = await rental_repo.save_head_info(
            user_id=current_user.id,
            rental_id=str(rental_id),
            payload=data.data,
            existing_rental=None
        )
        
        updated_rental = await updated_rental.to_dict()
        
        logger.info(
            f"Created head info for new rental {rental_id}",
            extra={
                "rental_id": str(rental_id),
                "user_id": current_user.id
            }
        )
        
        return HeadInfoResponse(
            data=updated_rental,
            message="Head information created successfully",
            success=True
        )
        
    except PermissionError:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to update this rental"
        )
        
    except ValidationError as ve:
        logger.warning(
            f"Validation error updating head info for rental {rental_id}",
            extra={"errors": ve.errors()}
        )
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid data provided",
                "errors": ve.errors()
            }
        )
        
    except IntegrityError as e:
        logger.error(
            f"Integrity error updating head info for rental {rental_id}",
            exc_info=e,
            extra={"rental_id": str(rental_id)}
        )
        
        error_msg = str(e).lower()
        if 'slug' in error_msg or 'unique' in error_msg:
            raise HTTPException(
                status_code=409,
                detail="A rental with similar information already exists. Please try a different title."
            )
        elif 'foreign key' in error_msg or 'publisher_id' in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Invalid user reference. Please check your account."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Database constraint violation. Please check your input data."
            )
            
    except Exception as e:
        logger.error(
            f"Unexpected error updating head info for rental {rental_id}",
            exc_info=e,
            extra={"rental_id": str(rental_id), "user_id": current_user.id}
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while updating head information. Please try again later."
        )
        
             
@rental_router.post("/{rental_id}/location")
@limiter.limit("100/minute")
async def update_location(
    request: Request,
    rental_id: str,
    data: LocationCreate,
    current_user: User = Depends(get_current_user)
):
    """Update rental location endpoint"""
    try:
    
        rental_repo = get_rental_repo()
        
        rental = await rental_repo.get_by_id_with_owner_check(
            rental_id=str(rental_id),
            user_id=current_user.id
        )
        

        if not rental:  
            raise HTTPException(status_code=404, detail="Rental not found")
        
        # Save location
        result = await rental_repo.save_location_info(
            user_id=str(current_user.id),
            rental_id=str(rental_id),
            payload=data,
            existing_rental=rental
        )
        
        # Check result
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return {
            "success": True,
            "message": result["message"],
            # "data": result["data"].get_location_summary()
        }
    except Exception as err:
        logger.exception(err)    
        
@rental_router.post("/{rental_id}/pricing")
@limiter.limit("100/minute")
async def update_pricing(
    request: Request,
    rental_id: str,
    data: PriceCreate,
    current_user: User = Depends(get_current_user)
):
    """Update rental pricing information."""
    try:
        rental_repo = get_rental_repo()
           
        rental = await rental_repo.get_by_id_with_owner_check(
            rental_id=str(rental_id),
            user_id=current_user.id
        )
        

        if not rental:  
            raise HTTPException(status_code=404, detail="Rental not found")
        
        # Update pricing
        updated_pricing = await rental_repo.save_pricing(
            rental_id=str(rental_id),
            payload=data,
            existing_rental=rental
        )
        
        
        logger.info(f"Updated pricing for rental {rental_id}", extra={
            "user_id": current_user.id,
            "amount": data.amount,
            "currency": data.currency
        })
        if not updated_pricing.get('success'):
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while updating pricing"
            )
                
        
        return {
            "success": True,
            "message": "Pricing information updated successfully",
            "data": {
                "price": float(data.amount) if data.amount else None,
                "currency": data.currency,
                "period": data.period
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pricing for rental {rental_id}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while updating pricing"
        )


@rental_router.post("/{rental_id}/amenities")
@limiter.limit("100/minute")
async def update_amenities(
    request: Request,
    rental_id: str,
    amenities: List[AmenityCreate],
    current_user: User = Depends(get_current_user)
):
    """Update rental amenities."""
    try:
        rental_repo = get_rental_repo()
        
        rental = await rental_repo.get_by_id_with_owner_check(
            rental_id=str(rental_id),
            user_id=current_user.id
        )
        

        if not rental:  
            raise HTTPException(status_code=404, detail="Rental not found")
        
        # Update amenities
        response = await rental_repo.save_amenities(
            rental_id=str(rental_id),
            payload=amenities,
            existing_rental=rental
        )
        
        if not response.get('success'):
            raise HTTPException(status_code=500, detail=response.get('message') )
        
        
        return {
            "success": True,
            "message": f"Updated {len(amenities)} amenities successfully",
            "data": {
                "amenities": [amenity.dict() for amenity in amenities],
                "count": len(amenities)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating amenities for rental {rental_id}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while updating amenities"
        )


@rental_router.post("/{rental_id}/rules")
@limiter.limit("100/minute")
async def update_rules(
    request: Request,
    rental_id: str,
    rules: List[PropertyRuleCreate],
    current_user: User = Depends(get_current_user)
):
    """Update rental rules."""
    try:
        rental_repo = get_rental_repo()
        
        # Check permission
        rental = await rental_repo.get_by_id_with_owner_check(
            rental_id=str(rental_id),
            user_id=current_user.id
        )
        
        response = await rental_repo.save_rules(
            rental_id=str(rental_id),
            payload=rules,
            existing_rental=rental
        )
        
        if not response.get('success'):
            raise HTTPException(status_code=500, detail=response.get('message') )
        
        
        return {
            "success": True,
            "message": f"Updated rules successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rules for rental {rental_id}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while updating rules"
        )


@rental_router.post("/{rental_id}/files")
async def upload_files(
    request: Request,
    rental_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload files for a rental."""
    try:
        rental_repo = get_rental_repo()
        rental = await rental_repo.get_by_id_with_owner_check(
            rental_id=str(rental_id),
            user_id=current_user.id
        )
        

        if not rental:  
            raise HTTPException(status_code=404, detail="Rental not found")
        
        
        if len(files) > 40:
            raise HTTPException(status_code=400, detail="Maximum 20 files allowed per upload")
        
        uploaded_files = []
        for file in files:
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset pointer
            
            if file_size > 50 * 1024 * 1024:  # 50MB
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} exceeds 10MB limit"
                )
            
            allowed_types = ['image/jpeg', 'image/jpg','image/png', 'image/webp',  'video/mp4','video/webm','video/ogg',
            'video/quicktime''application/pdf']
            
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {file.content_type} not allowed"
                )
            
      
            results = await save_files_batch(
                files=files,
                folder="rentals",
                subfolder=f"{rental_id}",
                file_type="form"
            )
            
            # Filter successful uploads
            successful_results = [r for r in results if r.success]
            
            # Convert to database format
            db_data = save_files_batch_sync(
                files=successful_results,
                rental_id=rental_id,
                user_id=current_user.id
            )
            
            try:
                res =await get_rental_repo().addGalleryBatch(db_data)
                if res:
                    return {
                        "success": True,
                        "message": f"Uploaded {len(uploaded_files)} files successfully",
                        "data": {
                            "count": len(uploaded_files)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed  uploadin {len(uploaded_files)} files ",
                    }
            except Exception as err:
                logger.exception(err)
                raise HTTPException(
                    status_code=500,
                    detail="An unexpected error occurred while uploading files"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files for rental {rental_id}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while uploading files"
        )


@rental_router.post("/")
@limiter.limit("50/minute")
async def create_rental(
    request: Request,
    data: RentalCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new rental listing."""
    try:
        rental_repo = get_rental_repo()
        
        
        return {
            "success": True,
            "message": "Rental created successfully",
            # "data": {
            #     "rental": rental.get_property_summary(),
            #     "id": rental.id,
            #     "slug": rental.slug
            # }
        }

    except ValueError as e:
        logger.warning(f"Validation error creating rental: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error("Unexpected error creating rental", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the rental"
        )


# Public endpoint - accessible to everyone, optimized for SEO
@rental_router.get("/")
@limiter.limit("5/second")
async def list_rentals(
    request: Request,
    page: int = 1,
    limit: int = 20,
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
    filters: Optional[RentalFilter] =None
) :
    """
    Get all rentals (public endpoint).
    
    This endpoint is accessible to everyone and optimized for SEO.
    Returns a paginated list of rental properties.
    """
    try:
        rental_repo = get_rental_repo()
        
        if category:
            rentals = await rental_repo.filter_rentals(category=category)
          
        else:  
            rentals = await rental_repo.list_public_rentals(
                offset=page,
                limit=limit,
            )
            
        total_count = len(rentals)
        
        # print(f"Found data :", rentals)
        
        return {
            'success':True,
            'message':"Rentals retrieved successfully",
            'data':rentals,
            'pagination':{
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) 
            }
        }

    except ValueError as e:
        logger.warning(f"Validation error retrieving rentals: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error("Unexpected error retrieving rentals", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving rentals"
        )


@rental_router.get("/{public_id}/for-edit")
@limiter.limit("5/second")
async def get_rental_for_edit(request: Request, 
                              public_id: str,
                              current_user: User = Depends(get_current_user
                         )):
    try:
        rental_repo = get_rental_repo()
        
        if not  public_id:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
            
        rental = await rental_repo.get_by_public_id(public_id=public_id)
        if not rental:
            raise HTTPException(
                status_code=404,
                detail="Rental not found"
            )
        if rental.publisher_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to edit this rental"
            )           


        
        return {
            'success':True,
            'message':"Rental retrieved successfully",
            'data':rental_repo._rental_to_dict_for_edit(rental),
    
        }

        
    except Exception as e:
        logger.error("Unexpected error retrieving rentals", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving rentals"
        )

@rental_router.get("/slug/{slug}")
@limiter.limit("5/second")
async def get_rental_by_slug( request: Request,slug: str):
    try:
        rental_repo = get_rental_repo()
        
        if not  slug:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
            
        rentals = await rental_repo.filter_rentals(slug=slug)
        rental = rentals[0] if rentals else None
          
        
        return {
            'success':True,
            'message':"Rental retrieved successfully",
            'data':rental,
    
        }

        
    except Exception as e:
        logger.error("Unexpected error retrieving rentals", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving rentals"
        )


@rental_router.get("/{public_id}")
@limiter.limit("5/second")
async def get_rental_by_public_id( request: Request,public_id: str):
    try:
        rental_repo = get_rental_repo()
        
        if not  public_id:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
            
        rentals = await rental_repo.filter_rentals(public_id=public_id)
        rental = rentals[0] if rentals else None
          
        
        return {
            'success':True,
            'message':"Rental retrieved successfully",
            'data':rental,
    
        }

        
    except Exception as e:
        logger.error("Unexpected error retrieving rentals", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving rentals"
        )



# Personalized endpoint - requires user authentication
@rental_router.get("/personalized/{user_id}", response_model=ListRentalResponse)
@limiter.limit("3/second")
async def list_personalized_rentals(
    request: Request,
    user_id: str,
    page: int = 1,
    limit: int = 20,
    filters: Optional[RentalFilter] = Depends(),
    current_user: User = Depends(get_current_user)
) -> ListRentalResponse:
    """
    Get personalized rental recommendations for a specific user.
    
    Requires authentication. Returns rentals tailored to the user's
    preferences, search history, and behavior.
    """
    try:
        # Verify user authorization
        if current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this user's personalized rentals"
            )
        
        rental_repo = get_rental_repo()
        
        # Get personalized rentals based on user preferences
        rentals = await rental_repo.list_personalized_rentals(
            user_id=user_id,
            page=page,
            limit=limit,
            filters=filters
        )
        
        # Get total count for pagination
        total_count = await rental_repo.get_personalized_rental_count(
            user_id=user_id,
            filters=filters
        )
        
        return ListRentalResponse(
            success=True,
            message="Personalized rentals retrieved successfully",
            data=rentals,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error retrieving personalized rentals for user {user_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving personalized rentals for user {user_id}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving personalized rentals"
        )


# Featured rentals - accessible to both logged-in and logged-out users
@rental_router.get("/featured", response_model=ListRentalResponse)
@limiter.limit("1/second")
async def list_featured_rentals(
    request: Request,
    page: int = 1,
    limit: int = 10,
    user_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> ListRentalResponse:
    """
    Get featured rental listings.
    
    Accessible to both authenticated and anonymous users.
    Returns curated featured properties that are promoted or highlighted.
    """
    try:
        rental_repo = get_rental_repo()
        
        # Determine if we should personalize for logged-in users
        if current_user and user_id and current_user.id == user_id:
            # Get personalized featured rentals
            rentals = await rental_repo.list_personalized_featured_rentals(
                user_id=user_id,
                page=page,
                limit=limit
            )
            message = "Personalized featured rentals retrieved successfully"
        else:
            # Get general featured rentals for public/anonymous users
            rentals = await rental_repo.list_public_featured_rentals(
                page=page,
                limit=limit
            )
            message = "Featured rentals retrieved successfully"
        
        # Get total count for pagination
        total_count = await rental_repo.get_featured_rental_count(
            user_id=user_id if current_user else None
        )
        
        return ListRentalResponse(
            success=True,
            message=message,
            data=rentals,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error retrieving featured rentals: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error("Unexpected error retrieving featured rentals", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving featured rentals"
        )




# Featured rentals - accessible to both logged-in and logged-out users
@rental_router.get("/trending", response_model=ListRentalResponse)
@limiter.limit("1/second")
async def list_featured_rentals(
    request: Request,
    page: int = 1,
    limit: int = 10,
    user_id: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> ListRentalResponse:
    """
    Get featured rental listings.
    
    Accessible to both authenticated and anonymous users.
    Returns curated featured properties that are promoted or highlighted.
    """
    try:
        rental_repo = get_rental_repo()
        
        # Determine if we should personalize for logged-in users
        if current_user and user_id and current_user.id == user_id:
            # Get personalized featured rentals
            rentals = await rental_repo.list_personalized_featured_rentals(
                user_id=user_id,
                page=page,
                limit=limit
            )
            message = "Personalized featured rentals retrieved successfully"
        else:
            # Get general featured rentals for public/anonymous users
            rentals = await rental_repo.list_public_featured_rentals(
                page=page,
                limit=limit
            )
            message = "Featured rentals retrieved successfully"
        
        # Get total count for pagination
        total_count = await rental_repo.get_featured_rental_count(
            user_id=user_id if current_user else None
        )
        
        return ListRentalResponse(
            success=True,
            message=message,
            data=rentals,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error retrieving featured rentals: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error("Unexpected error retrieving featured rentals", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving featured rentals"
        )
        
        
        
# Interactive rentals - requires user authentication
@rental_router.get("/interactive/{user_id}", response_model=ListRentalResponse)
@limiter.limit("1/second")
async def list_interactive_rentals(
    request: Request,
    user_id: str,
    page: int = 1,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> ListRentalResponse:
    """
    Get interactive rental experiences.
    
    Requires authentication. Returns rentals with interactive features
    such as virtual tours, live Q&A, or real-time availability.
    """
    try:
        # Verify user authorization
        if current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this user's interactive rentals"
            )
        
        rental_repo = get_rental_repo()
        
        # Get interactive rentals
        rentals = await rental_repo.list_interactive_rentals(
            user_id=user_id,
            page=page,
            limit=limit
        )
        
        # Get total count for pagination
        total_count = await rental_repo.get_interactive_rental_count(user_id)
        
        return ListRentalResponse(
            success=True,
            message="Interactive rentals retrieved successfully",
            data=rentals,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        )

    except ValueError as e:
        logger.warning(f"Validation error retrieving interactive rentals for user {user_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving interactive rentals for user {user_id}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving interactive rentals"
        )





@rental_router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search term for autocomplete"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions to return")
):
    """
    Get search suggestions for autocomplete
    
    Returns:
        List of suggested search terms, locations, and categories
    """
    try:
        rental_repo = get_rental_repo()
        
        # Get suggestions from various sources
        suggestions = {
            "locations": await rental_repo.get_location_suggestions(q, limit),
            "categories": await rental_repo.get_category_suggestions(q, limit),
            "amenities": await rental_repo.get_amenity_suggestions(q, limit),
            "popular_searches": [
                "2 bedroom apartment in Nairobi",
                "studio with wifi",
                "house with parking",
                "affordable room near university"
            ]
        }
        
        return {
            "success": True,
            "query": q,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return {
            "success": False,
            "query": q,
            "suggestions": {},
            "error": "Failed to get suggestions"
        }
        
           

async def filter_mapper_to_db_search(payload: dict) -> dict:
    """
    Map parsed query entities to database filter parameters
    
    Args:
        payload: Dictionary containing parsed query results from get_query_parser
    
    Returns:
        Dictionary with database filter parameters
    """
    mapped_payload = {}
    
    # Extract entities from the parsed query
    entities = payload.get('entities', {})
    
    # Map bedrooms
    if 'bedrooms' in entities:
        mapped_payload['bedrooms'] = entities['bedrooms']
    
    # Map bathrooms
    if 'bathrooms' in entities:
        mapped_payload['bathrooms'] = entities['bathrooms']
    
    # Map price - handle different price formats
    if 'price' in entities:
        price_value = entities['price']
        if isinstance(price_value, dict) and 'min' in price_value and 'max' in price_value:
            # Price range
            mapped_payload['min_price'] = float(price_value['min'])
            mapped_payload['max_price'] = float(price_value['max'])
        elif isinstance(price_value, (int, float, str)):
            # Single price (treat as max price)
            try:
                price_num = float(price_value)
                mapped_payload['max_price'] = price_num
            except (ValueError, TypeError):
                pass
    
    # Map max_price
    elif 'max_price' in entities:
        try:
            mapped_payload['max_price'] = float(entities['max_price'])
        except (ValueError, TypeError):
            pass
    
    # Map price_range (format: "under 50000" or "30000-50000")
    elif 'price_range' in entities:
        price_range = str(entities['price_range'])
        if 'under' in price_range.lower():
            # Format: "under 50000"
            try:
                max_price = float(price_range.lower().replace('under', '').strip())
                mapped_payload['max_price'] = max_price
            except (ValueError, TypeError):
                pass
        elif '-' in price_range:
            # Format: "30000-50000"
            try:
                min_price, max_price = price_range.split('-')
                mapped_payload['min_price'] = float(min_price.strip())
                mapped_payload['max_price'] = float(max_price.strip())
            except (ValueError, TypeError):
                pass
    
    # Map location/city
    if 'location' in entities:
        location = entities['location']
        if isinstance(location, str):
            # Check if it's a known city or area
            # You might want to add logic here to distinguish between city and area
            mapped_payload['city'] = location.title()  # Capitalize first letter of each word
    
    # Map area (if separate from city)
    if 'area' in entities:
        area = entities['area']
        if isinstance(area, str):
            # If we have area but not city, we might need geocoding
            # For now, we'll treat area as city or implement area lookup
            mapped_payload['city'] = area.title()
    
    # Map amenities
    if 'amenities' in entities:
        amenities = entities['amenities']
        if isinstance(amenities, list):
            mapped_payload['amenities'] = amenities
        elif isinstance(amenities, str):
            mapped_payload['amenities'] = [amenities]
    
    # Map property type to category
    if 'property_type' in entities:
        property_type = entities['property_type'].lower()
        category_map = {
            'apartment': 'APARTMENT',
            'house': 'HOUSE', 
            'flat': 'APARTMENT',
            'condo': 'APARTMENT',
            'villa': 'HOUSE',
            'mansion': 'HOUSE',
            'cottage': 'HOUSE',
            'studio': 'STUDIO',
            'bedsitter': 'STUDIO',
            'bachelor': 'STUDIO',
            'single room': 'ROOM',
            'double room': 'ROOM',
            'self contained': 'APARTMENT'
        }
        if property_type in category_map:
            mapped_payload['category'] = category_map[property_type]
    
    # Map room_type to category
    elif 'room_type' in entities:
        room_type = entities['room_type'].lower()
        if room_type in ['studio', 'bedsitter', 'bachelor']:
            mapped_payload['category'] = 'STUDIO'
        elif room_type in ['single', 'double']:
            mapped_payload['category'] = 'ROOM'
    
    # Default filters
    mapped_payload['status'] = 'vacant'  # Only show active rentals
    mapped_payload['is_verified'] = True  # Only show verified rentals by default
    
    return mapped_payload


@rental_router.get("/search")
async def search_rentals(
    query: Optional[str] = None,
    lat: Optional[Decimal] = None,
    long: Optional[Decimal] = None,
    radius: Optional[float] = 10,
    category: Optional[List[str]] = Query(None),
    price_min: Optional[Decimal] = None,
    price_max: Optional[Decimal] = None,
    amenities: Optional[List[str]] = Query(None),
    property_type: Optional[List[str]] = Query(None),
    land_marks: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    country: Optional[str] = "KE",
    city: Optional[str] = None,
    state: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: Optional[str] = Query(None, description="Sort by: price_asc, price_desc, newest, featured"),
    is_featured: Optional[bool] = None,
    is_verified: Optional[bool] = True
):
    """
    Search rentals with natural language query and/or specific filters
    
    Example queries:
    - "2 bedroom apartment in Nairobi with wifi under 50000"
    - "studio near university with parking"
    - "house with garden and pool in Westlands"
    """
    try:
        rental_repo = get_rental_repo()
        
        # Initialize filter parameters
        filter_params = {
            'limit': page_size,
            'offset': (page - 1) * page_size
        }
        
        # Add explicit filter parameters if provided
        if category:
            filter_params['category'] = category[0] if len(category) == 1 else category
        
        if price_min is not None:
            filter_params['min_price'] = float(price_min)
        
        if price_max is not None:
            filter_params['max_price'] = float(price_max)
        
        if lat is not None and long is not None:
            filter_params['lat'] = lat
            filter_params['long'] = long
            filter_params['radius'] = radius
        
        if amenities:
            filter_params['amenities'] = amenities
        
        if status:
            filter_params['status'] = status[0] if len(status) == 1 else status
        
        if bedrooms is not None:
            filter_params['bedrooms'] = bedrooms
        
        if bathrooms is not None:
            filter_params['bathrooms'] = bathrooms
        
        if city:
            filter_params['city'] = city
        
        if state:
            filter_params['state'] = state
        
        if is_featured is not None:
            filter_params['is_featured'] = is_featured
        
        if is_verified is not None:
            filter_params['is_verified'] = is_verified
        
        # Process natural language query if provided
        parsed_query = None
        if query:
            parsed_query = await get_query_parser(query)
            
            if parsed_query.get('success', False):
                # Map parsed entities to database filters
                query_filters = await filter_mapper_to_db_search(parsed_query)
                
                # Merge query filters with explicit filters
                # Query filters take precedence for overlapping fields
                for key, value in query_filters.items():
                    if key not in filter_params or filter_params[key] is None:
                        filter_params[key] = value
        
        # Apply sorting
        if sort_by:
            # You might need to extend your repository to handle sorting
            # For now, we'll just pass it as a parameter
            filter_params['sort_by'] = sort_by
        
        # Execute search
        
        data = await rental_repo.filter_rentals(**filter_params)
        
        # Calculate pagination info
        total_results = len(data)
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 1
        
        return {
            "success": True,
            "message": "Search completed successfully",
            "query": query,
            "parsed_query": parsed_query,
            "filters_applied": filter_params,
            "data": {
                "results": data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_results": total_results,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            }
        }

    except ValueError as e:
        logger.warning(f"Validation error in search: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error("Unexpected error in search", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while searching rentals"
        )

        
    