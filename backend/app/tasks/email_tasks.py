"""
Email-related Celery tasks.
"""
from typing import List
from celery import shared_task
from app.core.logging import get_logger


logger = get_logger(__name__)


@shared_task(name="app.tasks.email.send_email")
def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None
) -> dict:
    """
    Send email task.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body

    Returns:
        Task result with status
    """
    try:
        # TODO: Implement actual email sending
        # For now, just log it
        logger.info(
            "email_sent",
            to=to_email,
            subject=subject,
        )

        return {
            "status": "success",
            "to": to_email,
            "subject": subject,
        }
    except Exception as e:
        logger.error(
            "email_send_failed",
            to=to_email,
            subject=subject,
            error=str(e),
        )
        raise


@shared_task(name="app.tasks.email.send_bulk_email")
def send_bulk_email(
    recipients: List[str],
    subject: str,
    body: str,
    html_body: str | None = None
) -> dict:
    """
    Send bulk emails.

    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body

    Returns:
        Task result with statistics
    """
    success_count = 0
    failed_count = 0

    for recipient in recipients:
        try:
            send_email.delay(recipient, subject, body, html_body)
            success_count += 1
        except Exception as e:
            logger.error("bulk_email_send_failed", recipient=recipient, error=str(e))
            failed_count += 1

    return {
        "total": len(recipients),
        "success": success_count,
        "failed": failed_count,
    }


@shared_task(name="app.tasks.email.send_verification_email")
def send_verification_email(email: str, token: str) -> dict:
    """Send email verification email."""
    verification_url = f"https://example.com/verify-email?token={token}"

    body = f"""
    Please verify your email address by clicking the link below:

    {verification_url}

    This link will expire in 48 hours.
    """

    html_body = f"""
    <html>
        <body>
            <h2>Verify Your Email</h2>
            <p>Please verify your email address by clicking the button below:</p>
            <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
                Verify Email
            </a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 48 hours.</p>
        </body>
    </html>
    """

    return send_email(email, "Verify Your Email", body, html_body)


@shared_task(name="app.tasks.email.send_password_reset_email")
def send_password_reset_email(email: str, token: str) -> dict:
    """Send password reset email."""
    reset_url = f"https://example.com/reset-password?token={token}"

    body = f"""
    You requested a password reset. Click the link below to reset your password:

    {reset_url}

    If you didn't request this, please ignore this email.
    This link will expire in 24 hours.
    """

    html_body = f"""
    <html>
        <body>
            <h2>Reset Your Password</h2>
            <p>You requested a password reset. Click the button below to reset your password:</p>
            <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px;">
                Reset Password
            </a>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>This link will expire in 24 hours.</p>
        </body>
    </html>
    """

    return send_email(email, "Reset Your Password", body, html_body)
