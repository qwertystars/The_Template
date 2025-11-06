"""User schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.core.validators import validate_password_strength


# Authentication Schemas
class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token."""
    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """Complete token response with refresh token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# User Creation
class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        return validate_password_strength(v)


# User Update
class UserUpdate(BaseModel):
    """User profile update request."""
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)


class PasswordUpdate(BaseModel):
    """Password update request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        return validate_password_strength(v)


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        return validate_password_strength(v)


# Email Verification
class EmailVerificationRequest(BaseModel):
    """Request email verification."""
    email: EmailStr


class EmailVerification(BaseModel):
    """Verify email with token."""
    token: str


# Two-Factor Authentication
class TwoFactorSetup(BaseModel):
    """2FA setup response."""
    secret: str
    qr_code: str  # base64 encoded QR code
    backup_codes: list[str]


class TwoFactorVerify(BaseModel):
    """Verify 2FA token."""
    token: str


class TwoFactorLogin(BaseModel):
    """Login with 2FA."""
    email: EmailStr
    password: str
    totp_token: str


# OAuth
class OAuthLogin(BaseModel):
    """OAuth login request."""
    provider: str
    code: str
    redirect_uri: str


# User Response
class UserResponse(BaseModel):
    """User response model."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_email_verified: bool
    is_2fa_enabled: bool
    roles: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    @classmethod
    def from_orm(cls, user: any) -> "UserResponse":
        """Create response from ORM model."""
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_email_verified=user.is_email_verified,
            is_2fa_enabled=user.is_2fa_enabled,
            roles=user.get_roles(),
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Admin schemas
class UserAdminUpdate(BaseModel):
    """Admin user update."""
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    roles: Optional[list[str]] = None
    permissions: Optional[list[str]] = None


# API Key Management
class APIKeyCreate(BaseModel):
    """Create API key."""
    name: str = Field(..., max_length=100)


class APIKeyResponse(BaseModel):
    """API key response."""
    api_key: str
    created_at: datetime


# Generic response
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None
