# schemas/request/admin.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
import re

class AdminCreate(BaseModel):
    user_id: str
    employee_id: str = Field(..., regex=r'^EMP-[A-Z0-9]{6,}$')
    admin_level: int = Field(ge=1, le=3)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    
    @validator('admin_level')
    def validate_admin_level(cls, v):
        if v not in [1, 2, 3]:  # SUPPORT, ADMIN, SUPER_ADMIN
            raise ValueError('Invalid admin level')
        return v

class AdminUpdate(BaseModel):
    employee_id: Optional[str] = Field(None, regex=r'^EMP-[A-Z0-9]{6,}$')
    admin_level: Optional[int] = Field(None, ge=1, le=3)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    permissions: Optional[Dict[str, Any]] = None
    
    @validator('employee_id')
    def validate_employee_id(cls, v):
        if v and not re.match(r'^EMP-[A-Z0-9]{6,}$', v):
            raise ValueError('Invalid employee ID format')
        return v

class PermissionUpdate(BaseModel):
    module: str
    action: str
    enabled: bool
    
    @validator('module')
    def validate_module(cls, v):
        valid_modules = ['user_management', 'property_management', 
                        'content_management', 'financial', 'reports', 'system']
        if v not in valid_modules:
            raise ValueError(f'Invalid module. Must be one of: {valid_modules}')
        return v
    
    
# schemas/request/admin.py - Add these
class AdminSearch(BaseModel):
    query: Optional[str] = None
    level: Optional[int] = None
    department: Optional[str] = None
    active_only: bool = True

class AdminSuspend(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    duration_days: Optional[int] = Field(None, ge=1, le=365)

# schemas/response/admin.py - Add these
class AdminActivity(BaseModel):
    timestamp: datetime
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None

class AdminStats(BaseModel):
    total_admins: int
    active_admins: int
    by_level: Dict[str, int]    