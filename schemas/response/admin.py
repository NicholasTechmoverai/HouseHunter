# schemas/response/admin.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator

class AdminPermission(BaseModel):
    view: bool = False
    create: bool = False
    edit: bool = False
    delete: bool = False
    approve: bool = False

class AdminPermissions(BaseModel):
    user_management: AdminPermission = Field(default_factory=AdminPermission)
    property_management: AdminPermission = Field(default_factory=AdminPermission)
    content_management: Dict[str, bool] = Field(default_factory=dict)
    financial: Dict[str, bool] = Field(default_factory=dict)
    reports: Dict[str, bool] = Field(default_factory=dict)
    system: Dict[str, bool] = Field(default_factory=dict)

class AdminPreferences(BaseModel):
    dashboard_layout: str = "default"
    email_notifications: bool = True
    default_sort: str = "newest"
    items_per_page: int = 50

class AdminProfile(BaseModel):
    id: str
    user_id: str
    employee_id: str
    admin_level: int
    department: Optional[str] = None
    job_title: Optional[str] = None
    is_active: bool
    is_suspended: bool
    permissions: AdminPermissions
    preferences: AdminPreferences
    last_activity: Optional[datetime] = None
    supervisor_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_super_admin(self) -> bool:
        return self.admin_level == 3  # Assuming SUPER_ADMIN = 3
    
    @property
    def can_manage_users(self) -> bool:
        return (self.permissions.user_management.view or 
                self.permissions.user_management.edit)

class AdminList(BaseModel):
    admins: List[AdminProfile]
    total: int
    page: int
    limit: int
    
    
    
class AdminCreate(BaseModel):
    user_id: str
    employee_id: str
    admin_level: int
    department: Optional[str] = None
    job_title: Optional[str] = None
    permissions: AdminPermissions
    preferences: Optional[AdminPreferences] = None  

class AdminUpdate(BaseModel):
    employee_id: str
    admin_level: int
    department: Optional[str] = None
    job_title: Optional[str] = None
    permissions: AdminPermissions
    preferences: Optional[AdminPreferences] = None    