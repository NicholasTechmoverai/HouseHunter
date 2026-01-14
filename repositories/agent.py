import re
from uuid import UUID
from typing import Optional, Dict, Any, List
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q
from datetime import datetime
from models.user.users import User
from core.settings import settings
from core.logger import setup_logger
logger = setup_logger(__name__)
from models.house_agents import Agent
from schemas.response.user import Lv1_Profile, FullProfile

UNALLOWED_USERNAMES = [
    "saved", "terms", "videos", "live", "notifications",
    "report", "faqs", "about", "contact", "reservations",
    "admin", "administrator", "root", "system", "support",
    "help", "info", "mail", "email", "webmaster",
    "user", "users", "account", "accounts", "profile"
]

def get_agent_repo():
    return AgentRepository()

class AgentRepository:
    def __init__(self, model=Agent):
        self.model = model

    async def to_dict(self, agent):
        # Call the instance method of the agent
        # return await agent.to_dict() 
        return await agent.to_dict(agent)

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        try:
            return await self.model.get(id=agent_id)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting agent by ID {agent_id}: {str(e)}")
            raise

    async def get_by_public_id(self, public_id: str) -> Optional[Agent]:
        try:
            return await self.model.get(public_id=public_id)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting user by public ID {public_id}: {str(e)}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[Agent]:
        try:
            return await self.model.get(email=email)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting agent by email {email}: {str(e)}")
            raise

    async def get_by_user_id(self, user_id: str) -> Optional[Agent]:
        try:
            return await self.model.get(user_id=user_id)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting agent by user_id {user_id}: {str(e)}")
            raise    

    async def get_by_phone(self, phone: str) -> Optional[Agent]:
        try:
            return await self.model.get(phone_number=phone)
        except DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting agent by phone {phone}: {str(e)}")
            raise    
    
    async def get_by_username(self, username: str) -> Optional[Agent]:
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
    
    async def find_user(self, identifier: str) -> Optional[Agent]:
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


    async def create_agent(self, **kwargs) -> Agent:
        try:
            agent = await self.model.create(**kwargs)
            return agent
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise

    async def update_agent(self, agent: Agent, **kwargs) -> Agent:
        try:
            for key, value in kwargs.items():
                setattr(agent, key, value)
            await agent.save()
            return agent
        except Exception as e:
            logger.error(f"Error updating agent ID {agent.id}: {str(e)}")
            raise

    async def delete_agent(self, agent: Agent) -> None:
        try:
            await agent.delete()
        except Exception as e:
            logger.error(f"Error deleting agent ID {agent.id}: {str(e)}")
            raise

    async def list_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        try:
            return await self.model.all().offset(skip).limit(limit)
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise

