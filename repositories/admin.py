# repositories/admin_repository.py
import re
from typing import Any, Dict, List, Optional
from uuid import UUID
from tortoise.expressions import Q

from .base_repository import BaseRepository
from models.user import AdminUser
from schemas.response.admin import AdminProfile, AdminCreate, AdminUpdate

def get_admin_repo():
    return AdminRepository()


class AdminRepository(BaseRepository[AdminUser, AdminProfile]):
    
    def __init__(self):
        super().__init__(AdminUser, AdminProfile)
    
    async def get_by_employee_id(self, employee_id: str) -> Optional[AdminUser]:
        return await self.model.get_or_none(employee_id=employee_id)
    
    async def get_by_user_id(self, user_id: str) -> Optional[AdminUser]:
        return await self.model.get_or_none(user_id=user_id)
    
    async def get_with_permissions(self, admin_id: str) -> Dict[str, Any]:
        admin = await self.get_by_id(admin_id)
        if not admin:
            return {}
        
        return {
            "admin": await self.to_schema(admin),
            "permissions": admin.permissions,
            "has_permissions": admin.can_manage_users
        }
    
    async def search_admins(
        self, 
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[AdminUser]:
        return await self.model.filter(
            Q(employee_id__icontains=query) |
            Q(department__icontains=query) |
            Q(job_title__icontains=query)
        ).offset(skip).limit(limit).all()
    
    async def update_admin(
        self, 
        admin_id: str, 
        data: Dict[str, Any]
    ) -> AdminUser:
        admin = await self.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin not found")
        
        return await self.update(admin, data)
    
    async def suspend_admin(
        self, 
        admin_id: str, 
        reason: str,
        suspended_by_id: str
    ) -> AdminUser:
        admin = await self.get_by_id(admin_id)
        if not admin:
            raise ValueError("Admin not found")
        
        await admin.suspend(reason, None)
        
        await admin.log_activity(
            "admin_suspended",
            {"suspended_by": suspended_by_id, "reason": reason}
        )
        
        return admin
    
    async def get_admins_by_level(
        self, 
        level: int,
        active_only: bool = True
    ) -> List[AdminUser]:
        query = self.model.filter(admin_level=level)
        if active_only:
            query = query.filter(is_active=True, is_suspended=False)
        
        return await query.all()
    
    async def validate_employee_id(self, employee_id: str) -> bool:
        return bool(re.match(r'^EMP-[A-Z0-9]{6,}$', employee_id))