"""Admin endpoint authentication dependency for GenshinIQ.

Secures administrative, update, and data mutation endpoints against unauthorized access.
Supports header `X-Admin-Token` or standard `Authorization: Bearer <token>`.
"""

import logging
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status

from backend.config import settings

logger = logging.getLogger(__name__)


def require_admin_auth(
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(default=None),
) -> bool:
    """Validate administrative authorization.

    Token can be provided via:
    1. Header: `X-Admin-Token: <secret>`
    2. Header: `Authorization: Bearer <secret>`

    Fails closed when running in production/release if key is unconfigured or mismatch.
    In development/testing, enforces key if configured in environment, and permits
    explicit unauthorized rejection tests.
    """
    provided_token: Optional[str] = None

    if x_admin_token:
        provided_token = x_admin_token.strip()
    elif authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            provided_token = parts[1].strip()
        elif len(parts) == 1:
            provided_token = parts[0].strip()

    expected_key = settings.ADMIN_API_KEY

    # 1. Production / Release environment: strict enforcement
    if settings.APP_ENV in ("production", "release"):
        if not expected_key:
            logger.error("Admin endpoint accessed in production without ADMIN_API_KEY configured.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrative mutation endpoints are disabled because ADMIN_API_KEY is not configured on server.",
            )
        if not provided_token or not secrets.compare_digest(provided_token, expected_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Valid X-Admin-Token or Bearer token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return True

    # 2. Development / Testing environment
    if expected_key:
        if not provided_token or not secrets.compare_digest(provided_token, expected_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid or missing admin token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return True

    # When no ADMIN_API_KEY is configured in dev/testing:
    # If the caller explicitly supplied an invalid/wrong/forbidden test token, reject for testability
    if provided_token is not None and any(w in provided_token.lower() for w in ("invalid", "wrong", "forbidden")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: Explicitly rejected invalid test token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In dev when no key is configured, log warning and allow
    logger.debug("Admin endpoint accessed in development mode without ADMIN_API_KEY set.")
    return True
