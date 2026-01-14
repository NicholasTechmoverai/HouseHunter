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
from repositories.agent import get_agent_repo
from repositories.user import get_user_repo
from core.logger import setup_logger
from core.security import get_current_user,get_optional_current_user
from models.user import User
from tortoise.exceptions import ValidationError, IntegrityError, DoesNotExist
from utils.image_save import save_files_batch,save_uploaded_file,save_files_batch_sync
from services.search_service import get_query_parser
from decimal import Decimal

logger = setup_logger(__name__)

agent_router = APIRouter(prefix="/agent", tags=["Agent"])


@agent_router.post("/{user_id}/init")
@limiter.limit("100/minute")
async def update_head_info(
    request: Request,
    user_id: str,
    # data: HeadInfoRecord,
    current_user: User = Depends(get_current_user)
) :
    try:

        user_repo = get_user_repo()
        agent_repo = get_agent_repo()
        agent = await agent_repo.get_by_user_id(current_user.id)
        if agent:
            return{
                "success": True,
                "message": "Agent profile already exists",
                "data": await agent_repo.to_dict(agent),
                "hasAnAccount": True,
            }

        user = await user_repo.get_by_public_id(current_user.public_id)
        user = user_repo._to_personal_dict(user)



        return {
            "success": True,
            "message": "Profile fetched successfully",
            "data": user,
            "hasAnAccount": False,
        }

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))





@agent_router.post("/profile")
@limiter.limit("100/minute")
async def update_head_info(
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


@agent_router.post("/{public_id}")
@limiter.limit("100/minute")
async def update_head_info(
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

