"""Utility functions for validation."""
import re


def validate_password_strength(password: str) -> str:
    """
    Validate password meets security requirements.

    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character

    Args:
        password: Password to validate

    Returns:
        The validated password

    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long')

    if not re.search(r'[A-Z]', password):
        raise ValueError('Password must contain at least one uppercase letter')

    if not re.search(r'[a-z]', password):
        raise ValueError('Password must contain at least one lowercase letter')

    if not re.search(r'\d', password):
        raise ValueError('Password must contain at least one number')

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError('Password must contain at least one special character')

    return password
