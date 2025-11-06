"""
Authentication endpoints including login, registration, password reset, and OAuth.
"""
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
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
    generate_totp_secret,
    get_totp_uri,
    generate_qr_code,
    verify_totp_token,
)
from app.core.config import settings
from app.core.logging import get_logger, audit_logger
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordReset,
    EmailVerificationRequest,
    EmailVerification,
    TwoFactorSetup,
    TwoFactorVerify,
    MessageResponse,
)
from app.api.deps import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a new user.

    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    - **full_name**: Optional full name
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_email_verified=not settings.ENABLE_EMAIL_VERIFICATION,
    )

    # Set default role
    user.set_roles(["user"])

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Send verification email if enabled
    if settings.ENABLE_EMAIL_VERIFICATION:
        token = create_email_verification_token(user.email)
        # TODO: Send email with token
        # background_tasks.add_task(send_verification_email, user.email, token)
        logger.info("verification_email_sent", user_id=user.id, email=user.email)

    audit_logger.log_auth_event(
        "user_registered",
        user_id=user.id,
        email=user.email,
    )

    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login.

    - **username**: Email address
    - **password**: User password
    """
    # Get user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        # Increment failed login attempts
        if user:
            user.increment_failed_login()
            await db.commit()

        audit_logger.log_auth_event(
            "login_failed",
            email=form_data.username,
            success=False,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is locked
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked due to too many failed login attempts",
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Check if 2FA is enabled
    if user.is_2fa_enabled:
        # Return partial token that requires 2FA
        # In a real implementation, you'd return a different token type
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA token required",
        )

    # Reset failed login attempts
    user.reset_failed_login()
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Create tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    audit_logger.log_auth_event(
        "login_success",
        user_id=user.id,
        email=user.email,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token
    """
    try:
        payload = decode_token(refresh_request.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Logout current user (client should discard tokens).

    In a production system, you'd add tokens to a blacklist in Redis.
    """
    audit_logger.log_auth_event(
        "logout",
        user_id=current_user.id,
        email=current_user.email,
    )

    return MessageResponse(message="Successfully logged out")


@router.post("/password-reset-request", response_model=MessageResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request password reset email.

    - **email**: User email address
    """
    result = await db.execute(select(User).where(User.email == reset_request.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if user:
        token = create_password_reset_token(user.email)
        # TODO: Send email with token
        # background_tasks.add_task(send_password_reset_email, user.email, token)
        logger.info("password_reset_requested", user_id=user.id, email=user.email)

    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/password-reset", response_model=MessageResponse)
async def reset_password(
    reset: PasswordReset,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Reset password using token from email.

    - **token**: Password reset token
    - **new_password**: New password
    """
    email = verify_password_reset_token(reset.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.hashed_password = get_password_hash(reset.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.reset_failed_login()  # Reset any lockouts

    await db.commit()

    audit_logger.log_auth_event(
        "password_reset",
        user_id=user.id,
        email=user.email,
    )

    return MessageResponse(message="Password has been reset successfully")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification: EmailVerification,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify email address using token.

    - **token**: Email verification token
    """
    email = verify_email_token(verification.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_email_verified:
        return MessageResponse(message="Email already verified")

    user.is_email_verified = True
    user.email_verified_at = datetime.utcnow()
    await db.commit()

    audit_logger.log_auth_event(
        "email_verified",
        user_id=user.id,
        email=user.email,
    )

    return MessageResponse(message="Email verified successfully")


@router.post("/verify-email/resend", response_model=MessageResponse)
async def resend_verification_email(
    request: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Resend email verification.

    - **email**: User email address
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user and not user.is_email_verified:
        token = create_email_verification_token(user.email)
        # TODO: Send email with token
        # background_tasks.add_task(send_verification_email, user.email, token)
        logger.info("verification_email_resent", user_id=user.id, email=user.email)

    return MessageResponse(message="Verification email sent if account exists")


# Two-Factor Authentication endpoints
@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Setup two-factor authentication for current user.
    """
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled",
        )

    # Generate TOTP secret
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)
    qr_code = generate_qr_code(uri)

    # Store secret (not enabled yet until verified)
    current_user.totp_secret = secret
    await db.commit()

    # Generate backup codes (in production, hash these)
    backup_codes = [f"{i:06d}" for i in range(100000, 100010)]

    return TwoFactorSetup(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes,
    )


@router.post("/2fa/verify", response_model=MessageResponse)
async def verify_2fa_setup(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify and enable 2FA with TOTP token.

    - **token**: 6-digit TOTP code
    """
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated",
        )

    if not verify_totp_token(current_user.totp_secret, verification.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token",
        )

    # Enable 2FA
    current_user.is_2fa_enabled = True
    await db.commit()

    audit_logger.log_security_event(
        "2fa_enabled",
        user_id=current_user.id,
        severity="info",
    )

    return MessageResponse(message="2FA enabled successfully")


@router.post("/2fa/disable", response_model=MessageResponse)
async def disable_2fa(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Disable 2FA (requires current TOTP token).

    - **token**: 6-digit TOTP code
    """
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled",
        )

    if not verify_totp_token(current_user.totp_secret, verification.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA token",
        )

    # Disable 2FA
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    await db.commit()

    audit_logger.log_security_event(
        "2fa_disabled",
        user_id=current_user.id,
        severity="warning",
    )

    return MessageResponse(message="2FA disabled successfully")
