from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    Body,
    status,
    Request,
)
from typing import List, Optional, Dict, Any
import traceback

from repositories.admin import AdminRepository, get_admin_repo
from core.security import AuthDependencies, require_scope_dependency, require_permission
from models.user import AdminLevel
from core.limiter import limiter
from core.logger import setup_logger
from repositories.as_admin import get_asadmin_repo,AsAdminRepository
from schemas.response.as_admin import Response, AdminUserListItem,AdminRentalListItem,BasicResponse

logger = setup_logger(__name__)
as_admin_router = APIRouter(
    prefix="/as-admin",
    tags=["Admin Management"],
    # dependencies=[Depends(AuthDependencies.get_current_superuser)]
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
        "traceback": traceback.format_exc(),
    }
    if admin_id:
        error_details["admin_id"] = admin_id

    logger.error("Admin API error", extra=error_details)

    if isinstance(error, HTTPException):
        raise error
    elif isinstance(error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@as_admin_router.get("/all-users", response_model=Response[AdminUserListItem])
@limiter.limit("30/minute")
async def get_all_users(
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    try:
        log_request("get_all_users")
        repo = get_asadmin_repo()

        users = await repo.get_all_users(limit=limit, offset=offset)

        return Response(
            success=True,
            message="Success",
            data=users,
            total=len(users),
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        handle_error("get_all_users", e)
        logger.exception(e)
        raise
      
@as_admin_router.get("/all-rentals",response_model=Response[AdminRentalListItem])
@limiter.limit("30/minute")
async def get_all_rentals(
    request: Request,
    limit: int = 20,
    offset: int = 0,
):
    try:
        log_request("get_all_rentals")
        repo = get_asadmin_repo()

        rentals = await repo.get_all_rentals(limit=limit, offset=offset)

        return Response(
            success=True,
            message="Success",
            data=rentals,
            total=len(rentals),
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        handle_error("get_all_users", e)
        logger.exception(e)
        raise
      
