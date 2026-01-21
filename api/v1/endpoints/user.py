from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Depends, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from core.limiter import limiter
from schemas.request.user import (
    EditProfile,
)
import json
from schemas.response.user import (
    FullProfile,UserPersonalProfile
)
from repositories.user import get_user_repo
from repositories.rentals import get_rental_repo
from core.logger import setup_logger
from core.security import get_current_user,get_optional_current_user
from models.user import User
from tortoise.exceptions import ValidationError, IntegrityError, DoesNotExist
from utils.image_save import save_files_batch,save_uploaded_file,save_files_batch_sync
from services.search_service import get_query_parser
from decimal import Decimal

logger = setup_logger(__name__)

user_router = APIRouter(prefix="/user", tags=["User"])




@user_router.post("/profile")
@limiter.limit("100/minute")
async def get_user_profile(
    request: Request,
    # data: HeadInfoRecord,
    current_user: User = Depends(get_current_user)
) :
    try:

        user_repo = get_user_repo()
        user = await user_repo.get_by_public_id(current_user.public_id)
        user = user_repo._to_personal_dict(user)

        return {
            "success": True,
            "message": "Profile fetched successfully",
            "data": user
        }

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))



@user_router.post("/{public_id}/profile")
@limiter.limit("100/minute")
async def update_user_profile(
    request: Request,
    public_id:str,
    data: EditProfile,
    current_user: User = Depends(get_current_user)
) :
    try:
        if current_user.public_id != public_id:
            raise HTTPException(status_code=400, detail="Unauthorized,Kidly login and try updating your profile!")

        user_repo = get_user_repo()
        user = await user_repo.update(current_user,data)
        user = user_repo._to_personal_dict(user)

        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": user
        }

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))

@user_router.post("/{public_id}/listings")
@limiter.limit("100/minute")
async def fetch_user_listings(
    request: Request,
    public_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_optional_current_user)
) :
    try:
        if not public_id:
            raise HTTPException(status_code=400, detail="Public ID is required")
        
        rental_repo = get_rental_repo()
    

        if current_user:
            user_id = current_user.id
        else:
            user = await get_user_repo().get_by_public_id(public_id)
            if not user:
                raise ValueError("User not found")
            user_id = user.id

        rentals = await rental_repo.get_user_rentals(user_id, limit=limit, offset=offset)

        return {
            "success": True,
            "message": "Profile fetched successfully",
            "data": {
                "rentals": rentals
            }
        }

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))




@user_router.post("/{public_id}")
@limiter.limit("100/minute")
async def get_user_profile_readonly(
    request: Request,
    public_id: str,
    current_user: User = Depends(get_optional_current_user)
) :
    try:
        if not public_id:
            raise HTTPException(status_code=400, detail="Public ID is required")
        
        user_repo = get_user_repo()
        user = await user_repo.get_by_public_id(public_id)
        user = user_repo._to_personal_dict(user)

        return {
            "success": True,
            "message": "Profile fetched successfully",
            "data": user
        }

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))

