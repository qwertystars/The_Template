"""
Comprehensive tests for app/models/user.py
"""
import pytest
from datetime import datetime, timedelta
import json

from app.models.user import User
from app.core.security import get_password_hash


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            email="newuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="New User",
        )
        
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_superuser is False

    def test_user_repr(self):
        """Test user string representation."""
        user = User(
            id=123,
            email="test@example.com",
            hashed_password="hashed",
        )
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert "123" in repr_str
        assert "test@example.com" in repr_str


class TestUserLocking:
    """Tests for account locking functionality."""

    def test_is_locked_when_not_locked(self):
        """Test is_locked returns False when account not locked."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        assert user.is_locked is False

    def test_is_locked_when_locked_and_not_expired(self):
        """Test is_locked returns True when account locked and not expired."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            locked_until=datetime.utcnow() + timedelta(minutes=10),
        )
        
        assert user.is_locked is True

    def test_is_locked_when_locked_but_expired(self):
        """Test is_locked returns False when lock expired."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            locked_until=datetime.utcnow() - timedelta(minutes=1),
        )
        
        assert user.is_locked is False

    def test_increment_failed_login(self):
        """Test incrementing failed login attempts."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            failed_login_attempts=0,
        )
        
        user.increment_failed_login()
        
        assert user.failed_login_attempts == 1
        assert user.locked_until is None

    def test_increment_failed_login_locks_after_five_attempts(self):
        """Test account locks after 5 failed attempts."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            failed_login_attempts=4,
        )
        
        user.increment_failed_login()
        
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
        assert user.is_locked is True

    def test_increment_failed_login_sets_30_minute_lock(self):
        """Test account locks for 30 minutes."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            failed_login_attempts=4,
        )
        
        before = datetime.utcnow()
        user.increment_failed_login()
        after = datetime.utcnow()
        
        expected_unlock = before + timedelta(minutes=30)
        # Allow 1 second tolerance
        assert abs((user.locked_until - expected_unlock).total_seconds()) < 1

    def test_reset_failed_login(self):
        """Test resetting failed login attempts."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            failed_login_attempts=3,
            locked_until=datetime.utcnow() + timedelta(minutes=10),
        )
        
        user.reset_failed_login()
        
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestUserRoles:
    """Tests for user roles functionality."""

    def test_get_roles_empty(self):
        """Test getting roles when none set."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        roles = user.get_roles()
        
        assert roles == []

    def test_set_roles_single(self):
        """Test setting single role."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        user.set_roles(["admin"])
        
        assert user.roles == '["admin"]'
        assert user.get_roles() == ["admin"]

    def test_set_roles_multiple(self):
        """Test setting multiple roles."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        user.set_roles(["admin", "moderator", "user"])
        
        roles = user.get_roles()
        assert len(roles) == 3
        assert "admin" in roles
        assert "moderator" in roles
        assert "user" in roles

    def test_get_roles_returns_list(self):
        """Test get_roles always returns list."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            roles='["role1", "role2"]',
        )
        
        roles = user.get_roles()
        
        assert isinstance(roles, list)
        assert roles == ["role1", "role2"]

    def test_set_roles_overwrites(self):
        """Test setting roles overwrites previous roles."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        user.set_roles(["role1"])
        user.set_roles(["role2", "role3"])
        
        roles = user.get_roles()
        assert roles == ["role2", "role3"]


class TestUserPermissions:
    """Tests for user permissions functionality."""

    def test_get_permissions_empty(self):
        """Test getting permissions when none set."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        perms = user.get_permissions()
        
        assert perms == []

    def test_set_permissions_single(self):
        """Test setting single permission."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        user.set_permissions(["users:read"])
        
        assert user.permissions == '["users:read"]'
        assert user.get_permissions() == ["users:read"]

    def test_set_permissions_multiple(self):
        """Test setting multiple permissions."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        user.set_permissions(["users:read", "users:write", "items:read"])
        
        perms = user.get_permissions()
        assert len(perms) == 3
        assert "users:read" in perms
        assert "users:write" in perms
        assert "items:read" in perms

    def test_get_permissions_returns_list(self):
        """Test get_permissions always returns list."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            permissions='["perm1", "perm2"]',
        )
        
        perms = user.get_permissions()
        
        assert isinstance(perms, list)
        assert perms == ["perm1", "perm2"]

    def test_set_permissions_overwrites(self):
        """Test setting permissions overwrites previous permissions."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
        )
        
        user.set_permissions(["perm1"])
        user.set_permissions(["perm2", "perm3"])
        
        perms = user.get_permissions()
        assert perms == ["perm2", "perm3"]


class TestUserEdgeCases:
    """Tests for edge cases in User model."""

    def test_user_with_all_optional_fields(self):
        """Test user with all optional fields populated."""
        user = User(
            email="full@example.com",
            hashed_password="hashed",
            full_name="Full Name",
            avatar_url="https://example.com/avatar.jpg",
            is_email_verified=True,
            email_verified_at=datetime.utcnow(),
            is_2fa_enabled=True,
            totp_secret="SECRETBASE32",
            oauth_provider="google",
            oauth_id="google123",
            api_key="api_key_12345",
            api_key_created_at=datetime.utcnow(),
        )
        
        assert user.full_name == "Full Name"
        assert user.avatar_url == "https://example.com/avatar.jpg"
        assert user.is_email_verified is True
        assert user.is_2fa_enabled is True

    def test_user_with_minimal_fields(self):
        """Test user with only required fields."""
        user = User(
            email="minimal@example.com",
            hashed_password="hashed",
        )
        
        assert user.email == "minimal@example.com"
        assert user.hashed_password == "hashed"
        assert user.is_active is True
        assert user.is_superuser is False

    def test_get_roles_with_invalid_json(self):
        """Test get_roles with invalid JSON raises error."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            roles="invalid json",
        )
        
        with pytest.raises(json.JSONDecodeError):
            user.get_roles()

    def test_get_permissions_with_invalid_json(self):
        """Test get_permissions with invalid JSON raises error."""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            permissions="invalid json",
        )
        
        with pytest.raises(json.JSONDecodeError):
            user.get_permissions()