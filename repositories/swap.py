
import re
from uuid import UUID
from typing import Optional, Dict, Any, List
from tortoise.exceptions import DoesNotExist
from tortoise.query_utils import Q

from models.user import User
from schemas.responce.user import Lv1_Profile, FullProfile

# Default unallowed usernames
UNALLOWED_USERNAMES = [
    "saved", "terms", "videos", "live", "notifications",
    "report", "faqs", "about", "contact", "reservations"
]


def get_user_repo():
    return UserRepository()


class UserRepository:
    def __init__(self, model=User):
        self.model = model

    # Basic Getters
    
    async def get_by_id(self, user_id: str):
        return await self.model.get(id=user_id)

    async def get_by_public_id(self, public_id: str):
        return await self.model.get(public_id=public_id)

    async def is_user_exists(self, verifier: str):
        """
        Check if a user exists by email or ID.
        Returns user object if found, None otherwise.
        """
        user = await self.model.get_or_none(Q(email=verifier) | Q(id=verifier))
        return user

    # Username Utilities
    async def get_unallowed_names(self) -> List[str]:
        return UNALLOWED_USERNAMES

    async def check_username_availability(
        self, username: str, user_id: Optional[UUID] = None
    ) -> bool:
        """
        Returns True if username is available or belongs to current user.
        """
        if not username or not re.fullmatch(r"^[a-zA-Z0-9_]{3,20}$", username):
            return False

        if username.lower() in [name.lower() for name in UNALLOWED_USERNAMES]:
            return False

        user = await self.model.get_or_none(username=username)
        if user:
            if user_id and user.id == user_id:
                return True  # allowed to keep current username
            return False  # taken by another user

        return True  # available

    # Profiles
    async def get_lv1_profile(self, user_id: str) -> Lv1_Profile:
        user = await self.get_by_id(user_id)
        return Lv1_Profile.model_validate(user.__dict__)

    async def get_full_profile(self, user_id: str) -> FullProfile:
        user = await self.get_by_id(user_id)
        return FullProfile.model_validate(user.__dict__)

    # CRUD Operations
    async def create(self, payload: Dict[str, Any]):
        return await self.model.create(**payload)

    async def update(self, user_obj, data: Dict[str, Any]):
        """
        Updates only the provided fields.
        Exclude None values to preserve defaults.
        """
        update_data = {k: v for k, v in data.items() if v is not None}
        for key, value in update_data.items():
            setattr(user_obj, key, value)
        await user_obj.save()
        return user_obj

    async def delete(self, user_id: str):
        user = await self.get_by_id(user_id)
        await user.delete()
        return True
