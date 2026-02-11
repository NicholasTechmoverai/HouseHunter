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
                "description" :'',
                "icon": 'i-lucide-home',
                "count" : None
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
    
@ui_utilities_router.get("/counties/{country_code}")
@limiter.limit("3/second")
async def get_counties(request: Request, country_code: str):
    """
    Retrieve counties for a given country code.

    Args:
        request (Request): FastAPI request object.
        country_code (str): ISO code of the country (e.g., "KE").

    Returns:
        dict: success status, message, and data list of counties.
    """
    if not country_code:
        raise HTTPException(
            status_code=400,
            detail="Country code is required."
        )

    try:
        from utils.main import KENYA_COUNTIES


        return {
            "success": True,
            "message": "",
            "data": KENYA_COUNTIES if country_code == 'KE' else []
        }

    except Exception as e:
        logger.error(f"Unexpected error retrieving counties for {country_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving counties."
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
    

@ui_utilities_router.get("/our-reviews")
@limiter.limit("3/second")
async def get_our_reviews(request: Request):
    unsplash_profiles = [
        "https://images.unsplash.com/photo-1494790108755-2616b786d49d?w=200&h=200&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&h=200&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&h=200&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1507591064344-4c6ce005-128?w=200&h=200&fit=crop&crop=face"
    ]
    
    temp_reviews = [
        {
            "rating": 4,
            "message": "HouseHunter made finding housing so easy! I found a perfect studio within walking distance of campus. The verification process gave me peace of mind.",
            "user": {
                "name": "Alex Mwangi",
                "location": "BU, Freshman",
                "profile_picture": unsplash_profiles[0]
            }
        },
        {
            "rating": 3,
            "message": "As an international student, I was worried about finding housing. This platform connected me with trusted landlords and I found my apartment in just 3 days!",
            "user": {
                "name": "Sarah Johnson",
                "location": "KU, International Student",
                "profile_picture": unsplash_profiles[1]
            }
        },
        {
            "rating": 5,
            "message": "The swap feature saved me so much money! I was able to exchange my apartment with another student when I transferred campuses. Highly recommended!",
            "user": {
                "name": "David Omondi",
                "location": "JKUAT, Senior",
                "profile_picture": unsplash_profiles[2]
            }
        }
    ]
    
    try:
        return {
            "success": True,
            "message": "Reviews retrieved successfully",
            "data": temp_reviews,
        }
    except Exception as e:
        logger.error("Unexpected error retrieving reviews", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving reviews"
        )