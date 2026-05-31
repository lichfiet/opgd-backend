import logging
import os
from typing import Optional

import httpx
from fastapi import HTTPException, status

from ._router import router
from shared.ses import send_contact_email
from routes.models import ContactRequest

logger = logging.getLogger(__name__)

RECAPTCHA_SECRET = os.environ.get("RECAPTCHA_SECRET_KEY")
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_MIN_SCORE = 0.5


async def verify_recaptcha(token: Optional[str]) -> bool:
    """Verify reCAPTCHA v3 token with Google. Returns True if valid or verification disabled."""
    if not RECAPTCHA_SECRET:
        return True
    if not token:
        return False
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                RECAPTCHA_VERIFY_URL,
                data={"secret": RECAPTCHA_SECRET, "response": token},
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
        if not data.get("success"):
            logger.warning("reCAPTCHA verification failed: %s", data)
            return False
        score = data.get("score", 0)
        if score < RECAPTCHA_MIN_SCORE:
            logger.warning("reCAPTCHA score too low: %s", score)
            return False
        return True
    except Exception as e:
        logger.exception("reCAPTCHA verify error: %s", e)
        return False


@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def contact(request: ContactRequest) -> dict:
    """
    Contact endpoint — sends a notification email to On Point Garage Doors.
    Requires valid reCAPTCHA v3 token when RECAPTCHA_SECRET_KEY is set.
    """
    if not await verify_recaptcha(request.recaptcha_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification failed. Please try again.",
        )
    try:
        response = send_contact_email(
            full_name=request.full_name,
            email=request.email,
            phone=request.phone,
            service=request.service,
            message=request.message,
        )

        return {
            "status": "success",
            "message": "Contact form submitted successfully",
            "message_id": response["MessageId"],
        }

    except Exception as e:
        logger.exception("Error processing contact form")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process contact form",
        )
