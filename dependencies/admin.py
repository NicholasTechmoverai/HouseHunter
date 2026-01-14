from fastapi import Depends, HTTPException, status
from repositories.user import UserRepository, get_user_repo

async def require_admin(
    user_repo: UserRepository = Depends(get_user_repo),
    token_data = Depends(get_current_user)  # however you authenticate
):
    # Pull user from DB
    user = await user_repo.get_by_public_id(token_data.public_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check user role
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Check approval status
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Admin not approved")

    return user
