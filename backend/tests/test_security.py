"""
Comprehensive tests for app/core/security.py
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    generate_api_key,
    generate_totp_secret,
    get_totp_uri,
    generate_qr_code,
    verify_totp_token,
    check_permissions,
    check_roles,
)
from app.core.config import settings


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_get_password_hash_returns_different_hash_each_time(self):
        """Test that same password generates different hashes."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert len(hash1) > 0
        assert len(hash2) > 0

    def test_verify_password_with_correct_password(self):
        """Test password verification with correct password."""
        password = "mySecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "mySecurePassword123!"
        wrong_password = "wrongPassword456"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_with_empty_string(self):
        """Test password verification with empty password."""
        password = "testpassword"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False

    def test_get_password_hash_with_special_characters(self):
        """Test hashing password with special characters."""
        password = "p@$$w0rd!#%&*()[]{}:<>?/"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_get_password_hash_with_unicode(self):
        """Test hashing password with unicode characters."""
        password = "пароль密码🔒"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token_default_expiration(self):
        """Test access token creation with default expiration."""
        user_id = "123"
        token = create_access_token(subject=user_id)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_access_token_custom_expiration(self):
        """Test access token creation with custom expiration."""
        user_id = "456"
        expire_delta = timedelta(minutes=5)
        token = create_access_token(subject=user_id, expires_delta=expire_delta)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expire_delta
        
        assert abs((exp_time - expected_time).total_seconds()) < 2

    def test_create_access_token_with_additional_claims(self):
        """Test access token with additional claims."""
        user_id = "789"
        additional_claims = {"email": "test@example.com", "role": "admin"}
        token = create_access_token(
            subject=user_id,
            additional_claims=additional_claims
        )
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = "999"
        token = create_refresh_token(subject=user_id)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_decode_token_valid(self):
        """Test decoding valid token."""
        user_id = "111"
        token = create_access_token(subject=user_id)
        
        payload = decode_token(token)
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_token_invalid(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_decode_token_expired(self):
        """Test decoding expired token."""
        user_id = "222"
        token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401

    def test_create_access_token_with_integer_subject(self):
        """Test token creation with integer subject."""
        user_id = 12345
        token = create_access_token(subject=user_id)
        
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)


class TestEmailVerificationTokens:
    """Tests for email verification tokens."""

    def test_create_email_verification_token(self):
        """Test email verification token creation."""
        email = "test@example.com"
        token = create_email_verification_token(email)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == email
        assert payload["type"] == "email_verification"

    def test_verify_email_token_valid(self):
        """Test verifying valid email token."""
        email = "verify@example.com"
        token = create_email_verification_token(email)
        
        result = verify_email_token(token)
        
        assert result == email

    def test_verify_email_token_invalid(self):
        """Test verifying invalid email token."""
        invalid_token = "invalid.token"
        
        result = verify_email_token(invalid_token)
        
        assert result is None

    def test_verify_email_token_wrong_type(self):
        """Test verifying token with wrong type."""
        email = "test@example.com"
        token = create_access_token(subject=email)  # Wrong type
        
        result = verify_email_token(token)
        
        assert result is None

    def test_verify_email_token_expired(self):
        """Test verifying expired email token."""
        email = "expired@example.com"
        expire = datetime.utcnow() + timedelta(seconds=-1)
        
        to_encode = {
            "exp": expire,
            "sub": email,
            "type": "email_verification"
        }
        token = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        result = verify_email_token(token)
        
        assert result is None


class TestPasswordResetTokens:
    """Tests for password reset tokens."""

    def test_create_password_reset_token(self):
        """Test password reset token creation."""
        email = "reset@example.com"
        token = create_password_reset_token(email)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == email
        assert payload["type"] == "password_reset"

    def test_verify_password_reset_token_valid(self):
        """Test verifying valid password reset token."""
        email = "reset@example.com"
        token = create_password_reset_token(email)
        
        result = verify_password_reset_token(token)
        
        assert result == email

    def test_verify_password_reset_token_invalid(self):
        """Test verifying invalid password reset token."""
        invalid_token = "invalid.reset.token"
        
        result = verify_password_reset_token(invalid_token)
        
        assert result is None

    def test_verify_password_reset_token_wrong_type(self):
        """Test verifying token with wrong type."""
        email = "test@example.com"
        token = create_email_verification_token(email)  # Wrong type
        
        result = verify_password_reset_token(token)
        
        assert result is None


class TestAPIKey:
    """Tests for API key generation."""

    def test_generate_api_key_unique(self):
        """Test that API keys are unique."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert key1 != key2
        assert len(key1) > 0
        assert len(key2) > 0

    def test_generate_api_key_length(self):
        """Test API key has reasonable length."""
        key = generate_api_key()
        
        # URL-safe base64 of 32 bytes should be ~43 characters
        assert len(key) > 40

    def test_generate_api_key_url_safe(self):
        """Test API key is URL-safe."""
        key = generate_api_key()
        
        # Should only contain URL-safe characters
        assert all(c.isalnum() or c in '-_' for c in key)


class TestTOTP:
    """Tests for TOTP (2FA) functionality."""

    def test_generate_totp_secret(self):
        """Test TOTP secret generation."""
        secret = generate_totp_secret()
        
        assert len(secret) == 32  # Base32 encoded
        assert secret.isupper()  # Base32 is uppercase
        assert secret.isalnum()

    def test_generate_totp_secret_unique(self):
        """Test that TOTP secrets are unique."""
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()
        
        assert secret1 != secret2

    def test_get_totp_uri(self):
        """Test TOTP URI generation."""
        secret = generate_totp_secret()
        email = "user@example.com"
        
        uri = get_totp_uri(secret, email)
        
        assert uri.startswith("otpauth://totp/")
        assert email in uri
        assert settings.APP_NAME in uri
        assert secret in uri

    def test_generate_qr_code(self):
        """Test QR code generation."""
        secret = generate_totp_secret()
        uri = get_totp_uri(secret, "test@example.com")
        
        qr_code = generate_qr_code(uri)
        
        assert len(qr_code) > 0
        # Should be base64 encoded
        import base64
        decoded = base64.b64decode(qr_code)
        assert len(decoded) > 0

    def test_verify_totp_token_valid(self):
        """Test TOTP token verification with valid token."""
        import pyotp
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        assert verify_totp_token(secret, token) is True

    def test_verify_totp_token_invalid(self):
        """Test TOTP token verification with invalid token."""
        secret = generate_totp_secret()
        invalid_token = "000000"
        
        assert verify_totp_token(secret, invalid_token) is False

    def test_verify_totp_token_wrong_secret(self):
        """Test TOTP token with wrong secret."""
        import pyotp
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()
        
        totp = pyotp.TOTP(secret1)
        token = totp.now()
        
        assert verify_totp_token(secret2, token) is False


class TestPermissionsAndRoles:
    """Tests for permission and role checking."""

    def test_check_permissions_all_granted(self):
        """Test permission check when all permissions are granted."""
        required = ["users:read", "users:write"]
        user_perms = ["users:read", "users:write", "items:read"]
        
        assert check_permissions(required, user_perms) is True

    def test_check_permissions_missing_one(self):
        """Test permission check when one permission is missing."""
        required = ["users:read", "users:write", "users:delete"]
        user_perms = ["users:read", "users:write"]
        
        assert check_permissions(required, user_perms) is False

    def test_check_permissions_empty_required(self):
        """Test permission check with empty required list."""
        required = []
        user_perms = ["users:read"]
        
        assert check_permissions(required, user_perms) is True

    def test_check_permissions_empty_user_permissions(self):
        """Test permission check with empty user permissions."""
        required = ["users:read"]
        user_perms = []
        
        assert check_permissions(required, user_perms) is False

    def test_check_roles_has_role(self):
        """Test role check when user has required role."""
        required = ["admin", "moderator"]
        user_roles = ["user", "admin"]
        
        assert check_roles(required, user_roles) is True

    def test_check_roles_missing_role(self):
        """Test role check when user missing all required roles."""
        required = ["admin", "moderator"]
        user_roles = ["user", "viewer"]
        
        assert check_roles(required, user_roles) is False

    def test_check_roles_empty_required(self):
        """Test role check with empty required list."""
        required = []
        user_roles = ["user"]
        
        assert check_roles(required, user_roles) is False

    def test_check_roles_empty_user_roles(self):
        """Test role check with empty user roles."""
        required = ["admin"]
        user_roles = []
        
        assert check_roles(required, user_roles) is False

    def test_check_roles_multiple_matches(self):
        """Test role check with multiple matching roles."""
        required = ["admin", "moderator", "editor"]
        user_roles = ["admin", "moderator"]
        
        assert check_roles(required, user_roles) is True