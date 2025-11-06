"""
Comprehensive tests for app/api/deps.py
"""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    require_roles,
    require_permissions,
    PaginationParams,
    get_pagination_params,
)
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session, test_user):
        """Test getting current user with valid token."""
        token = create_access_token(subject=str(test_user.id))
        
        user = await get_current_user(token=token, db=db_session)
        
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Test getting current user with invalid token."""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=db_session)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session):
        """Test getting current user when user doesn't exist in DB."""
        token = create_access_token(subject="99999")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, db_session):
        """Test getting current user when user is inactive."""
        user = User(
            email="inactive@example.com",
            hashed_password="hashed",
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        token = create_access_token(subject=str(user.id))
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 403
        assert "Inactive user" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_locked_account(self, db_session):
        """Test getting current user when account is locked."""
        user = User(
            email="locked@example.com",
            hashed_password="hashed",
            is_active=True,
            locked_until=datetime.utcnow() + timedelta(minutes=30),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        token = create_access_token(subject=str(user.id))
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 403
        assert "locked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_wrong_token_type(self, db_session, test_user):
        """Test getting current user with refresh token (wrong type)."""
        token = create_refresh_token(subject=str(test_user.id))
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self, test_user):
        """Test getting active user when user is active."""
        user = await get_current_active_user(current_user=test_user)
        
        assert user == test_user

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test getting active user when user is inactive."""
        inactive_user = User(
            email="inactive@example.com",
            hashed_password="hashed",
            is_active=False,
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=inactive_user)
        
        assert exc_info.value.status_code == 403


class TestGetCurrentSuperuser:
    """Tests for get_current_superuser dependency."""

    @pytest.mark.asyncio
    async def test_get_current_superuser_is_superuser(self, test_superuser):
        """Test getting superuser when user is superuser."""
        user = await get_current_superuser(current_user=test_superuser)
        
        assert user == test_superuser
        assert user.is_superuser is True

    @pytest.mark.asyncio
    async def test_get_current_superuser_not_superuser(self, test_user):
        """Test getting superuser when user is not superuser."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_superuser(current_user=test_user)
        
        assert exc_info.value.status_code == 403
        assert "Not enough permissions" in exc_info.value.detail


class TestRequireRoles:
    """Tests for require_roles dependency factory."""

    @pytest.mark.asyncio
    async def test_require_roles_user_has_role(self, test_user):
        """Test role requirement when user has required role."""
        test_user.set_roles(["admin", "user"])
        
        checker = require_roles("admin")
        user = await checker(current_user=test_user)
        
        assert user == test_user

    @pytest.mark.asyncio
    async def test_require_roles_user_missing_role(self, test_user):
        """Test role requirement when user missing required role."""
        test_user.set_roles(["user"])
        
        checker = require_roles("admin")
        
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=test_user)
        
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_roles_multiple_roles(self, test_user):
        """Test multiple role requirement."""
        test_user.set_roles(["moderator", "user"])
        
        checker = require_roles("admin", "moderator")
        user = await checker(current_user=test_user)
        
        assert user == test_user

    @pytest.mark.asyncio
    async def test_require_roles_no_roles(self, test_user):
        """Test role requirement when user has no roles."""
        test_user.set_roles([])
        
        checker = require_roles("admin")
        
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=test_user)
        
        assert exc_info.value.status_code == 403


class TestRequirePermissions:
    """Tests for require_permissions dependency factory."""

    @pytest.mark.asyncio
    async def test_require_permissions_user_has_all(self, test_user):
        """Test permission requirement when user has all permissions."""
        test_user.set_permissions(["users:read", "users:write", "items:read"])
        
        checker = require_permissions("users:read", "users:write")
        user = await checker(current_user=test_user)
        
        assert user == test_user

    @pytest.mark.asyncio
    async def test_require_permissions_user_missing_one(self, test_user):
        """Test permission requirement when user missing one permission."""
        test_user.set_permissions(["users:read"])
        
        checker = require_permissions("users:read", "users:write")
        
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=test_user)
        
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_permissions_no_permissions(self, test_user):
        """Test permission requirement when user has no permissions."""
        test_user.set_permissions([])
        
        checker = require_permissions("users:read")
        
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=test_user)
        
        assert exc_info.value.status_code == 403


class TestPaginationParams:
    """Tests for PaginationParams class."""

    def test_pagination_params_default(self):
        """Test pagination with default parameters."""
        params = PaginationParams()
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0
        assert params.limit == 20

    def test_pagination_params_custom(self):
        """Test pagination with custom parameters."""
        params = PaginationParams(page=3, page_size=50)
        
        assert params.page == 3
        assert params.page_size == 50
        assert params.offset == 100
        assert params.limit == 50

    def test_pagination_params_negative_page(self):
        """Test pagination with negative page defaults to 1."""
        params = PaginationParams(page=-5)
        
        assert params.page == 1
        assert params.offset == 0

    def test_pagination_params_zero_page(self):
        """Test pagination with zero page defaults to 1."""
        params = PaginationParams(page=0)
        
        assert params.page == 1
        assert params.offset == 0

    def test_pagination_params_negative_page_size(self):
        """Test pagination with negative page size defaults to 1."""
        params = PaginationParams(page_size=-10)
        
        assert params.page_size == 1

    def test_pagination_params_zero_page_size(self):
        """Test pagination with zero page size defaults to 1."""
        params = PaginationParams(page_size=0)
        
        assert params.page_size == 1

    def test_pagination_params_max_page_size(self):
        """Test pagination caps page size at 100."""
        params = PaginationParams(page_size=500)
        
        assert params.page_size == 100
        assert params.limit == 100

    def test_pagination_params_offset_calculation(self):
        """Test offset calculation for various pages."""
        params1 = PaginationParams(page=1, page_size=10)
        params2 = PaginationParams(page=5, page_size=10)
        params3 = PaginationParams(page=10, page_size=25)
        
        assert params1.offset == 0
        assert params2.offset == 40
        assert params3.offset == 225

    def test_get_pagination_params_function(self):
        """Test get_pagination_params dependency function."""
        params = get_pagination_params(page=2, page_size=15)
        
        assert isinstance(params, PaginationParams)
        assert params.page == 2
        assert params.page_size == 15