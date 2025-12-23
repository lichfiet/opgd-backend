import logging

from fastapi import HTTPException, status

from ._router import router
from shared.ses import send_contact_email
from routes.models import ContactRequest

logger = logging.getLogger(__name__)

@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def contact(request: ContactRequest) -> dict:
    """
    Contact endpoint — sends a notification email to On Point Garage Doors.
    """
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
