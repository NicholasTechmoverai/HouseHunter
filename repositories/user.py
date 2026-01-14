import re
from uuid import UUID
from typing import Optional, Dict, Any, List
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from datetime import datetime
from core.settings import settings
from core.logger import setup_logger
logger = setup_logger(__name__)
from models.user import User,UserStatus,AccountType
from schemas.response.user import Lv1_Profile, FullProfile

UNALLOWED_USERNAMES = [
    "saved", "terms", "videos", "live", "notifications",
    "report", "faqs", "about", "contact", "reservations",
    "admin", "administrator", "root", "system", "support",
    "help", "info", "mail", "email", "webmaster",
    "user", "users", "account", "accounts", "profile"
]

def get_user_repo():
    return UserRepository()

class UserRepository:
    def __init__(self, model=User):
        self.model = model
    
    async def to_dict(self, user):
        # Call the instance method of the user
        # return await user.to_dict() 
        return self.model.to_dict(user)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            return await self.model.get(id=user_id)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            raise
    
    async def get_by_public_id(self, public_id: str) -> Optional[User]:
        try:
            return await self.model.get(public_id=public_id)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by public ID {public_id}: {str(e)}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            return await self.model.get(email=email)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise

    async def get_by_phone(self, phone: str) -> Optional[User]:
        try:
            return await self.model.get(phone_number=phone)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by phone {phone}: {str(e)}")
            raise    
    
    async def get_by_username(self, username: str) -> Optional[User]:
        try:
            return await self.model.get(username=username)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            raise
    
    async def exists(self, identifier: str) -> bool:
        try:
            user = await self.model.get(
                Q(email=identifier) | 
                Q(id=identifier) | 
                Q(username=identifier) |
                Q(public_id=identifier)
            )
            return True
        except DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error checking if user exists {identifier}: {str(e)}")
            raise
    
    async def find_user(self, identifier: str) -> Optional[User]:
        try:
            return await self.model.get(
                Q(email=identifier) | 
                Q(id=identifier) | 
                Q(username=identifier) |
                Q(public_id=identifier)
            )
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error finding user {identifier}: {str(e)}")
            raise
    
    async def get_unallowed_usernames(self) -> List[str]:
        try:
            return UNALLOWED_USERNAMES
        except Exception as e:
            logger.error(f"Error getting unallowed usernames: {str(e)}")
            raise
    
    def validate_username_format(self, username: str) -> bool:
        try:
            pattern = r"^[a-zA-Z][a-zA-Z0-9_]{2,19}$"
            return bool(re.fullmatch(pattern, username))
        except Exception as e:
            logger.error(f"Error validating username format {username}: {str(e)}")
            raise
    
    def is_reserved_username(self, username: str) -> bool:
        try:
            return username.lower() in [name.lower() for name in UNALLOWED_USERNAMES]
        except Exception as e:
            logger.error(f"Error checking reserved username {username}: {str(e)}")
            raise
    
    async def is_username_available(self, username: str, exclude_user_id: Optional[UUID] = None) -> Dict[str, Any]:
        try:
            if not self.validate_username_format(username):
                return {"available": False, "reason": "invalid_format"}
            
            if self.is_reserved_username(username):
                return {"available": False, "reason": "reserved"}
            
            existing_user = await self.get_by_username(username)
            
            if not existing_user:
                return {"available": True, "reason": None}
            
            if exclude_user_id and existing_user.id == exclude_user_id:
                return {"available": True, "reason": "owned_by_user"}
            
            return {"available": False, "reason": "taken"}
        except Exception as e:
            logger.error(f"Error checking username availability {username}: {str(e)}")
            raise
    
    async def authenticate(self, email: str, password: str, ip_address: str = None) -> Optional[User]:
        try:
            user = await self.get_by_email(email)
            
            if not user:
                return {"success": False, "user": None, "message": "Invalid email or password"}
            
            if user.locked_until and user.locked_until > datetime.utcnow():
                return {"success": False, "user": None, "message": f"Account is locked until {user.locked_until}. Please try again later."}
            
            if user.check_password(password):
                await user.reset_failed_logins()
                await user.update_last_login(ip_address)
                return {"success": True, "user": self.model.to_dict(user), "message": "Authentication successful"}
            
            await user.increment_failed_login()
            return None
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {str(e)}")
            raise
    
    async def register(self, email: str, first_name: str, password: Optional[str] = None, **kwargs):
        try:
            existing_email = await self.get_by_email(email)
            if existing_email:
                return {
                    "success": False,
                    "user": None,
                    "message": "Email already registered"
                }
            
            if kwargs.get("phone_number"):
                existing_phone = await self.model.get_or_none(phone_number=kwargs["phone_number"])
                if existing_phone:
                    return {
                        "success": False,
                        "user": None,
                        "message": "Phone number already registered"
                    }
            
            user_data = {
                "email": email,
                "first_name": first_name,
                "signup_ip": kwargs.get("signup_ip"),
                "signup_user_agent": kwargs.get("signup_user_agent"),
                **kwargs
            }
            
            user = await self.create(user_data)
            
            if password:
                user.set_password(password)
                
            await user.save()
            
            return {
                "success": True,
                "user": self.model.to_dict(user),
                "message": "Registration successful"
            }
        except Exception as e:
            logger.error(f"Error registering user {email}: {str(e)}")
            return {
                "success": False,
                "user": None,
                "message": f"Registration failed: {str(e)}"
            }
    
    async def create(self, data: Dict[str, Any]) -> User:
        try:
            return await self.model.create(**data)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def update(self, user: User, data: Dict[str, Any]) -> User:
        try:
            update_fields = []
            
            for key, value in data.items():
                if hasattr(user, key) and value is not None:
                    current_value = getattr(user, key)
                    if current_value != value:
                        setattr(user, key, value)
                        update_fields.append(key)
            
            if update_fields:
                await user.save(update_fields=update_fields)
            
            return user
        except Exception as e:
            logger.error(f"Error updating user {user.id}: {str(e)}")
            raise
    
    async def update_email(self, user: User, new_email: str) -> User:
        try:
            existing_user = await self.get_by_email(new_email)
            if existing_user and existing_user.id != user.id:
                raise ValueError("Email already in use")
            
            user.email = new_email
            user.email_verified = False
            user.email_verified_at = None
            await user.save(update_fields=["email", "email_verified", "email_verified_at"])
            return user
        except Exception as e:
            logger.error(f"Error updating email for user {user.id}: {str(e)}")
            raise
    
    async def update_username(self, user: User, new_username: str) -> User:
        try:
            username_check = await self.is_username_available(new_username, exclude_user_id=user.id)
            if not username_check["available"]:
                raise ValueError(f"Username not available: {username_check['reason']}")
            
            user.username = new_username
            await user.save(update_fields=["username"])
            return user
        except Exception as e:
            logger.error(f"Error updating username for user {user.id}: {str(e)}")
            raise
    
    async def change_password(self, user: User, current_password: str, new_password: str) -> User:
        try:
            if not user.check_password(current_password):
                raise ValueError("Current password is incorrect")
            
            user.set_password(new_password)
            await user.save(update_fields=[
                "password_hash", 
                "password_salt", 
                "last_password_changed", 
                "password_changed_count"
            ])
            return user
        except Exception as e:
            logger.error(f"Error changing password for user {user.id}: {str(e)}")
            raise
    
    async def reset_password(self, user: User, new_password: str) -> User:
        try:
            user.set_password(new_password)
            await user.save(update_fields=[
                "password_hash", 
                "password_salt", 
                "last_password_changed", 
                "password_changed_count"
            ])
            return user
        except Exception as e:
            logger.error(f"Error resetting password for user {user.id}: {str(e)}")
            raise
    
    async def verify_email(self, user: User) -> User:
        try:
            await user.verify_email()
            return user
        except Exception as e:
            logger.error(f"Error verifying email for user {user.id}: {str(e)}")
            raise
    
    async def deactivate_account(self, user: User, reason: str = "") -> User:
        try:
            await user.deactivate_account(reason)
            return user
        except Exception as e:
            logger.error(f"Error deactivating account for user {user.id}: {str(e)}")
            raise
    
    async def get_profile(self, user_id: str, full: bool = False) -> Optional[Dict[str, Any]]:
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            if full:
                profile_schema = FullProfile
            else:
                profile_schema = Lv1_Profile
            
            profile = profile_schema.model_validate(user)
            return profile.model_dump()
        except Exception as e:
            logger.error(f"Error getting profile for user {user_id}: {str(e)}")
            raise
    
    async def search_users(self, query: str, limit: int = 20, offset: int = 0) -> List[User]:
        try:
            search_filter = Q(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(display_name__icontains=query)
            )
            
            users = await self.model.filter(search_filter).limit(limit).offset(offset).all()
            return users
        except Exception as e:
            logger.error(f"Error searching users with query {query}: {str(e)}")
            raise
    
    async def count_users(self, filters: Optional[Dict[str, Any]] = None) -> int:
        try:
            query = self.model.all()
            
            if filters:
                conditions = []
                if filters.get("status"):
                    conditions.append(Q(status=filters["status"]))
                if filters.get("account_type"):
                    conditions.append(Q(account_type=filters["account_type"]))
                if filters.get("country"):
                    conditions.append(Q(country=filters["country"]))
                if filters.get("email_verified") is not None:
                    conditions.append(Q(email_verified=filters["email_verified"]))
                
                if conditions:
                    combined_condition = conditions[0]
                    for condition in conditions[1:]:
                        combined_condition &= condition
                    query = query.filter(combined_condition)
            
            return await query.count()
        except Exception as e:
            logger.error(f"Error counting users with filters {filters}: {str(e)}")
            raise
    
    async def get_users_by_status(self, status: int, limit: int = 50, offset: int = 0) -> List[User]:
        try:
            return await self.model.filter(status=status).limit(limit).offset(offset).all()
        except Exception as e:
            logger.error(f"Error getting users by status {status}: {str(e)}")
            raise
    
    async def get_recently_active(self, hours: int = 24, limit: int = 100) -> List[User]:
        try:
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return await self.model.filter(
                last_active__gte=cutoff_time,
                status=1
            ).order_by("-last_active").limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recently active users: {str(e)}")
            raise
    
    async def delete(self, user_id: str, soft_delete: bool = True) -> bool:
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            if soft_delete:
                user.is_deleted = True
                user.deleted_at = datetime.utcnow()
                await user.save()
            else:
                await user.delete()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            raise


    def _to_personal_dict(self, user: User) -> Dict[str, Any]:
        site_info = settings.SITE    
        user_status = UserStatus(user.account_type)
        current_account = AccountType(user.account_type)


        user = {
            "id": str(user.id),
            "public_id": str(user.public_id),
            "name": f"{user.first_name} {user.last_name}".strip(),
            "profile_picture": user.profile_picture if 'https://' in user.profile_picture else f"{site_info.FILE_READ_API}/{user.profile_picture}" if user.profile_picture else None,
            "profile_picture_thumbnail": user.profile_picture_thumbnail if 'https://' in user.profile_picture_thumbnail else f"{site_info.FILE_READ_API}/{user.profile_picture_thumbnail}" if user.profile_picture_thumbnail else None,
            "email": {
                "email": user.email,
                "email_verified": user.email_verified,
            },
            "username": user.username,
            "display_name": user.display_name,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "gender": user.gender,
            "phone_number":{
                "country_code": user.phone_country_code,
                "number": user.phone_number,
                "phone_verified": user.phone_verified,
            },
            "bio": user.bio,
            "website": user.website,
            "tagline": user.tagline,
            "occupation": user.occupation,
            "current_city": user.current_city,
            "current_country": user.current_country,
            "occupation": user.occupation,
            "company": user.company,
            "job_title": user.job_title,
            "industry": user.industry,
            "location": {
                "city": user.current_city,
                "country": user.current_country,
                "address": user.current_address,
                "county": user.current_county,
                "coordinates": {
                    "lat": float(user.current_latitude) if user.current_latitude else None,
                    "long": float(user.current_longitude) if user.current_longitude else None,
                },

            },
            "status": user_status.name,
            "account": {
                    "currentAccount": current_account.name,
                    "availableAccounts": [],
            },
            "last_active": user.last_active.isoformat() if user.last_active else None,
            "currency": user.currency,
            "locale": user.locale,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        return user