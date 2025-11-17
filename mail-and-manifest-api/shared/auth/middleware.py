import os
import logging
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)

# Admin password from environment
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me_in_production")


def verify_admin_password(authorization: Optional[str] = Header(None)) -> bool:
    """
    Verify admin password from Authorization header.

    Args:
        authorization: Authorization header value (Bearer token format)

    Returns:
        bool: True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Expected format: "Bearer <password>"
    try:
        scheme, password = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify password
    if password != ADMIN_PASSWORD:
        logger.warning(f"Failed authentication attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials"
        )

    logger.info("Admin authenticated successfully")
    return True
