from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from typing import List, Optional, Dict, Any
import traceback

from repositories.admin import AdminRepository,get_admin_repo
from schemas.request.admin import AdminCreate, AdminUpdate, PermissionUpdate, AdminSuspend
from schemas.response.admin import AdminProfile, AdminList, AdminActivity, AdminStats
from core.security import AuthDependencies, require_scope_dependency, require_permission
from models.user import AdminLevel
from core.limiter import limiter
from core.logger import setup_logger

logger = setup_logger(__name__)
admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin Management"],
    dependencies=[Depends(AuthDependencies.get_current_superuser)]
)


require_user_management = require_scope_dependency("admin:users:manage")
require_permission_management = require_scope_dependency("admin:permissions:manage")

def log_request(operation: str, admin_id: str = None, extra: Dict[str, Any] = None):
    log_data = {"operation": operation}
    if admin_id:
        log_data["admin_id"] = admin_id
    if extra:
        log_data.update(extra)
    logger.info("Admin API request", extra=log_data)

def handle_error(operation: str, error: Exception, admin_id: str = None):
    error_details = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc()
    }
    if admin_id:
        error_details["admin_id"] = admin_id
    
    logger.error("Admin API error", extra=error_details)
    
    if isinstance(error, HTTPException):
        raise error
    elif isinstance(error, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@admin_router.get("/dashboard", response_model=AdminStats)
@limiter.limit("30/minute")
async def get_dashboard_stats(repo: AdminRepository = Depends(get_admin_repo)):
    try:
        log_request("get_dashboard_stats")
        
        stats = {
            "total_admins": await repo.model.all().count(),
            "active_admins": await repo.model.filter(is_active=True, is_suspended=False).count(),
            "by_level": {
                "support": await repo.model.filter(admin_level=AdminLevel.SUPPORT.value).count(),
                "admin": await repo.model.filter(admin_level=AdminLevel.ADMIN.value).count(),
                "super_admin": await repo.model.filter(admin_level=AdminLevel.SUPER_ADMIN.value).count(),
            }
        }
        
        logger.debug(f"Dashboard stats retrieved: {stats}")
        return AdminStats(**stats)
        
    except Exception as e:
        handle_error("get_dashboard_stats", e)

@admin_router.post("/", response_model=AdminProfile, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_admin(
    admin_data: AdminCreate,
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("create_admin", extra={"employee_id": admin_data.employee_id})
        
        existing_employee = await repo.get_by_employee_id(admin_data.employee_id)
        if existing_employee:
            logger.warning(f"Duplicate employee ID attempt: {admin_data.employee_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
        
        existing_user = await repo.get_by_user_id(admin_data.user_id)
        if existing_user:
            logger.warning(f"Duplicate admin profile attempt for user: {admin_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has admin profile"
            )
        
        admin = await repo.create(admin_data.dict())
        logger.info(f"Admin created successfully: {admin.id}")
        
        return await repo.to_schema(admin)
        
    except Exception as e:
        handle_error("create_admin", e)

@admin_router.get("/", response_model=AdminList)
@limiter.limit("60/minute")
async def list_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    level: Optional[int] = Query(None, ge=1, le=3),
    active_only: bool = Query(True),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("list_admins", extra={
            "skip": skip, 
            "limit": limit, 
            "level": level, 
            "active_only": active_only
        })
        
        query = repo.model.all()
        
        if level:
            query = query.filter(admin_level=level)
        if active_only:
            query = query.filter(is_active=True, is_suspended=False)
        
        total = await query.count()
        admins = await query.offset(skip).limit(limit).all()
        
        admin_profiles = [await repo.to_schema(admin) for admin in admins]
        
        logger.debug(f"Listed {len(admin_profiles)} admins out of {total}")
        
        return AdminList(
            admins=admin_profiles,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            limit=limit
        )
        
    except Exception as e:
        handle_error("list_admins", e)

@admin_router.get("/search", response_model=List[AdminProfile])
@limiter.limit("30/minute")
async def search_admins(
    query: str = Query(..., min_length=2, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("search_admins", extra={"search_query": query, "skip": skip, "limit": limit})
        
        admins = await repo.search_admins(query, skip, limit)
        results = [await repo.to_schema(admin) for admin in admins]
        
        logger.debug(f"Search returned {len(results)} results for query: '{query}'")
        return results
        
    except Exception as e:
        handle_error("search_admins", e)

@admin_router.get("/{admin_id}", response_model=AdminProfile)
@limiter.limit("30/minute")
async def get_admin(
    admin_id: str = Path(..., min_length=1),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("get_admin", admin_id)
        
        admin = await repo.get_by_id(admin_id)
        if not admin:
            logger.warning(f"Admin not found: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        logger.debug(f"Admin retrieved: {admin_id}")
        return await repo.to_schema(admin)
        
    except Exception as e:
        handle_error("get_admin", e, admin_id)

@admin_router.get("/user/{user_id}", response_model=AdminProfile)
@limiter.limit("30/minute")
async def get_admin_by_user(
    user_id: str = Path(..., min_length=1),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("get_admin_by_user", extra={"user_id": user_id})
        
        admin = await repo.get_by_user_id(user_id)
        if not admin:
            logger.warning(f"Admin not found for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found for this user"
            )
        
        logger.debug(f"Admin retrieved for user: {user_id} -> {admin.id}")
        return await repo.to_schema(admin)
        
    except Exception as e:
        handle_error("get_admin_by_user", e)

@admin_router.put("/{admin_id}", response_model=AdminProfile)
@limiter.limit("20/minute")
async def update_admin(
    admin_id: str = Path(..., min_length=1),
    update_data: AdminUpdate = Body(...),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("update_admin", admin_id, extra={"update_fields": update_data.dict(exclude_none=True)})
        
        if update_data.employee_id:
            existing = await repo.get_by_employee_id(update_data.employee_id)
            if existing and str(existing.id) != admin_id:
                logger.warning(f"Employee ID conflict: {update_data.employee_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Employee ID already in use"
                )
        
        admin = await repo.update_admin(admin_id, update_data.dict(exclude_none=True))
        if not admin:
            logger.warning(f"Admin not found for update: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        logger.info(f"Admin updated successfully: {admin_id}")
        return await repo.to_schema(admin)
        
    except Exception as e:
        handle_error("update_admin", e, admin_id)

@admin_router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_admin(
    admin_id: str = Path(..., min_length=1),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("delete_admin", admin_id)
        
        admin = await repo.get_by_id(admin_id)
        if not admin:
            logger.warning(f"Admin not found for deletion: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        if admin.admin_level == AdminLevel.SUPER_ADMIN.value:
            logger.warning(f"Attempt to delete super admin: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete super admin"
            )
        
        await repo.delete(admin)
        logger.info(f"Admin deleted successfully: {admin_id}")
        
        return None
        
    except Exception as e:
        handle_error("delete_admin", e, admin_id)

@admin_router.post("/{admin_id}/permissions", response_model=AdminProfile)
@limiter.limit("15/minute")
async def update_admin_permissions(
    admin_id: str = Path(..., min_length=1),
    permission_data: PermissionUpdate = Body(...),
    repo: AdminRepository = Depends(get_admin_repo),
    _ = Depends(require_permission_management)
):
    try:
        log_request("update_admin_permissions", admin_id, extra={"permission_data": permission_data.dict()})
        
        admin = await repo.get_by_id(admin_id)
        if not admin:
            logger.warning(f"Admin not found for permission update: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        current_permissions = admin.permissions.copy()
        module_perms = current_permissions.get(permission_data.module, {})
        module_perms[permission_data.action] = permission_data.enabled
        current_permissions[permission_data.module] = module_perms
        
        await repo.update(admin, {"permissions": current_permissions})
        
        await admin.log_activity(
            "permissions_updated",
            {
                "updated_by": "system",
                "module": permission_data.module,
                "action": permission_data.action,
                "enabled": permission_data.enabled
            }
        )
        
        logger.info(f"Permissions updated for admin {admin_id}: {permission_data.module}.{permission_data.action}={permission_data.enabled}")
        
        return await repo.to_schema(admin)
        
    except Exception as e:
        handle_error("update_admin_permissions", e, admin_id)

@admin_router.post("/{admin_id}/suspend", response_model=AdminProfile)
@limiter.limit("10/minute")
async def suspend_admin(
    admin_id: str = Path(..., min_length=1),
    suspend_data: AdminSuspend = Body(...),
    repo: AdminRepository = Depends(get_admin_repo),
    current_admin = Depends(AuthDependencies.get_current_user)
):
    try:
        log_request("suspend_admin", admin_id, extra={
            "suspended_by": str(current_admin.id),
            "reason": suspend_data.reason
        })
        
        admin = await repo.get_by_id(admin_id)
        if not admin:
            logger.warning(f"Admin not found for suspension: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        if admin.admin_level == AdminLevel.SUPER_ADMIN.value:
            logger.warning(f"Attempt to suspend super admin: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot suspend super admin"
            )
        
        await repo.suspend_admin(admin_id, suspend_data.reason, str(current_admin.id))
        logger.info(f"Admin suspended: {admin_id} by {current_admin.id}")
        
        suspended_admin = await repo.get_by_id(admin_id)
        return await repo.to_schema(suspended_admin)
        
    except Exception as e:
        handle_error("suspend_admin", e, admin_id)

@admin_router.post("/{admin_id}/unsuspend", response_model=AdminProfile)
@limiter.limit("10/minute")
async def unsuspend_admin(
    admin_id: str = Path(..., min_length=1),
    repo: AdminRepository = Depends(get_admin_repo),
    _ = Depends(require_user_management)
):
    try:
        log_request("unsuspend_admin", admin_id)
        
        admin = await repo.get_by_id(admin_id)
        if not admin:
            logger.warning(f"Admin not found for unsuspension: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        await admin.unsuspend()
        logger.info(f"Admin unsuspended: {admin_id}")
        
        return await repo.to_schema(admin)
        
    except Exception as e:
        handle_error("unsuspend_admin", e, admin_id)

@admin_router.get("/{admin_id}/activity", response_model=List[AdminActivity])
@limiter.limit("30/minute")
async def get_admin_activity(
    admin_id: str = Path(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("get_admin_activity", admin_id, extra={"limit": limit})
        
        admin = await repo.get_by_id(admin_id)
        if not admin:
            logger.warning(f"Admin not found for activity retrieval: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        activities = admin.activity_log[:limit] if hasattr(admin, 'activity_log') else []
        logger.debug(f"Retrieved {len(activities)} activities for admin: {admin_id}")
        
        return [AdminActivity(**activity) for activity in activities]
        
    except Exception as e:
        handle_error("get_admin_activity", e, admin_id)

@admin_router.get("/levels/{level}", response_model=List[AdminProfile])
@limiter.limit("30/minute")
async def get_admins_by_level(
    level: int = Path(..., ge=1, le=3),
    active_only: bool = Query(True),
    repo: AdminRepository = Depends(get_admin_repo)
):
    try:
        log_request("get_admins_by_level", extra={"level": level, "active_only": active_only})
        
        admins = await repo.get_admins_by_level(level, active_only)
        results = [await repo.to_schema(admin) for admin in admins]
        
        logger.debug(f"Retrieved {len(results)} admins at level {level}")
        return results
        
    except Exception as e:
        handle_error("get_admins_by_level", e)