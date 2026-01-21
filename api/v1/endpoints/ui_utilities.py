from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Depends, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from core.limiter import limiter

from core.logger import setup_logger
from core.security import get_current_user,get_optional_current_user
from models.user import User
from models.defaults.property_catogories import PropertyCategory
import pycountry
from phonenumbers.phonenumberutil import country_code_for_region

logger = setup_logger(__name__)

ui_utilities_router = APIRouter(
    prefix="/utilities",
    tags=["Utility"]
)

@ui_utilities_router.post("/{rental_id}/head-info")
@limiter.limit("100/minute")
async def update_head_info(
    request: Request,
    rental_id: UUID,
    # data: HeadInfoRecord,
    current_user: User = Depends(get_current_user)
) :
    try:
        print()
            
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
        
        
@ui_utilities_router.get("/property-categories")
@limiter.limit("3/second")
async def get_property_categories(request: Request):
    try:
        data = [
            {
                "value": category.value,
                "key": category.name,
                "label": category.name.replace("_", " ").title(),
            }
            for category in PropertyCategory
        ]

        return {
            "success": True,
            "message": "",
            "data": data,
        }

    except Exception as e:
        logger.error("Unexpected error retrieving property categories", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving property categories"
        )


@ui_utilities_router.get("/countries")
@limiter.limit("3/second")
async def get_countries(request: Request):
    try:
        result = []

        for c in pycountry.countries:
            dial = country_code_for_region(c.alpha_2)
            if dial == 0:
                continue

            result.append({
                "id": c.alpha_2,
                "name": c.name,
                "dialCode": f"+{dial}",
                "emoji": "".join(chr(127397 + ord(x)) for x in c.alpha_2),
                # "isoCode": c.alpha_2,
                
            })

        return {
            "success": True,
            "message": "",
            "data": result,
        }

    except Exception as e:
        logger.error("Unexpected error retrieving countries", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving countries"
        )
    



@ui_utilities_router.get("/currencies")
@limiter.limit("3/second")
async def get_currencies(request: Request):
    try:
        from utils.defined import CURRENCY_LIST
        return {
            "success": True,
            "message": "",
            "data": CURRENCY_LIST,
        }

    except Exception as e:
        logger.error("Unexpected error retrieving countries", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving countries"
        )
    
@ui_utilities_router.get("/allowed-genders")
@limiter.limit("3/second")
async def get_allowed_genders(request: Request):
    try:
        from models.user.base_user import Gender
        data = [{"value": gender.value, "label": gender.name.replace("_", " ").title()} for gender in Gender]

        return {
            "success": True,
            "message": "",
            "data": data,
        }

    except Exception as e:
        logger.error("Unexpected error retrieving genders", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving genders"
        )