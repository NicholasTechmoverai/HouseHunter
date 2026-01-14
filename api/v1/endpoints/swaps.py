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

swaps_router = APIRouter(
    prefix="/rental",
    tags=["Rental"]
)

@swaps_router.post("/{rental_id}/head-info")
@limiter.limit("100/minute")
async def update_head_info(
    request: Request,
    rental_id: UUID,
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
        