"""
User management endpoints.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password
from app.core.logging import audit_logger
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    PasswordUpdate,
    UserListResponse,
    UserAdminUpdate,
    MessageResponse,
)
from app.api.deps import (
    get_current_user,
    get_current_superuser,
    get_pagination_params,
    PaginationParams,
)


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user profile."""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update current user profile.

    - **full_name**: Updated full name
    - **avatar_url**: Updated avatar URL
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url

    await db.commit()
    await db.refresh(current_user)

    audit_logger.log_data_access(
        "user",
        "update",
        user_id=current_user.id,
        resource_id=current_user.id,
    )

    return UserResponse.from_orm(current_user)


@router.put("/me/password", response_model=MessageResponse)
async def update_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update current user password.

    - **current_password**: Current password for verification
    - **new_password**: New password
    """
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_update.new_password)
    await db.commit()

    audit_logger.log_security_event(
        "password_changed",
        user_id=current_user.id,
        severity="info",
    )

    return MessageResponse(message="Password updated successfully")


@router.delete("/me", response_model=MessageResponse)
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete current user account (soft delete).
    """
    from datetime import datetime

    # Soft delete
    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False
    await db.commit()

    audit_logger.log_data_access(
        "user",
        "delete",
        user_id=current_user.id,
        resource_id=current_user.id,
    )

    return MessageResponse(message="Account deleted successfully")


# Admin endpoints
@router.get("", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all users (admin only).

    Supports pagination.
    """
    # Get total count
    count_result = await db.execute(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )
    total = count_result.scalar_one()

    # Get users
    result = await db.execute(
        select(User)
        .where(User.deleted_at.is_(None))
        .offset(pagination.offset)
        .limit(pagination.limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    # Calculate total pages
    pages = (total + pagination.page_size - 1) // pagination.page_size

    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get user by ID (admin only)."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserAdminUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update user (admin only).

    - **is_active**: Activate/deactivate user
    - **is_superuser**: Grant/revoke superuser status
    - **roles**: Update user roles
    - **permissions**: Update user permissions
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    if user_update.is_superuser is not None:
        user.is_superuser = user_update.is_superuser

    if user_update.roles is not None:
        user.set_roles(user_update.roles)

    if user_update.permissions is not None:
        user.set_permissions(user_update.permissions)

    await db.commit()
    await db.refresh(user)

    audit_logger.log_admin_action(
        "user_updated",
        user_id=current_user.id,
        target_user_id=user.id,
    )

    return UserResponse.from_orm(user)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete user (admin only, soft delete)."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Soft delete
    from datetime import datetime
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    await db.commit()

    audit_logger.log_admin_action(
        "user_deleted",
        user_id=current_user.id,
        target_user_id=user.id,
    )

    return MessageResponse(message="User deleted successfully")
