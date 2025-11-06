"""
Security utilities for authentication, authorization, and cryptography.
Includes password hashing, JWT token management, and OAuth2 support.
"""
from datetime import datetime, timedelta
from typing import Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict[str, Any]] = None
) -> str:
    """
    Create JWT access token.

    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Token expiration time
        additional_claims: Additional claims to include in token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """
    Create JWT refresh token with longer expiration.

    Args:
        subject: The subject of the token (usually user ID)
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def create_email_verification_token(email: str) -> str:
    """Create token for email verification."""
    expire = datetime.utcnow() + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    )

    to_encode = {
        "exp": expire,
        "sub": email,
        "type": "email_verification"
    }

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_email_token(token: str) -> Optional[str]:
    """Verify email verification token and return email."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create token for password reset."""
    expire = datetime.utcnow() + timedelta(
        hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )

    to_encode = {
        "exp": expire,
        "sub": email,
        "type": "password_reset"
    }

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


# Two-Factor Authentication (2FA) with TOTP
def generate_totp_secret() -> str:
    """Generate a new TOTP secret for 2FA."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Get TOTP provisioning URI for QR code generation."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.APP_NAME
    )


def generate_qr_code(uri: str) -> str:
    """Generate QR code image as base64 string."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")

    return base64.b64encode(buffered.getvalue()).decode()


def verify_totp_token(secret: str, token: str) -> bool:
    """Verify TOTP token."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


# Rate limiting helpers
class RateLimiter:
    """Simple rate limiter using Redis (to be implemented with Redis)."""

    def __init__(self, redis_client: Any):
        self.redis = redis_client

    async def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if a key has exceeded rate limit.

        Args:
            key: Unique identifier (e.g., user_id, ip_address)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
        """
        current = await self.redis.get(key)

        if current is None:
            await self.redis.setex(key, window_seconds, 1)
            return False

        if int(current) >= max_requests:
            return True

        await self.redis.incr(key)
        return False


def check_permissions(
    required_permissions: list[str],
    user_permissions: list[str]
) -> bool:
    """
    Check if user has required permissions.

    Args:
        required_permissions: List of required permission strings
        user_permissions: List of user's permission strings
    """
    return all(perm in user_permissions for perm in required_permissions)


def check_roles(required_roles: list[str], user_roles: list[str]) -> bool:
    """
    Check if user has any of the required roles.

    Args:
        required_roles: List of required role strings
        user_roles: List of user's role strings
    """
    return any(role in user_roles for role in required_roles)
