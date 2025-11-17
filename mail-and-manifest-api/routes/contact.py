import logging

from fastapi import HTTPException, status

from ._router import router
from .models import ContactRequest
from shared.ses.models import EmailService

logger = logging.getLogger(__name__)

@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def contact(request: ContactRequest) -> dict:
    """
    Contact endpoint - sends email via SES.

    Args:
        request: Contact form data

    Returns:
        dict: Success response with message ID
    """
    try:
        # Send notification email to business
        response = EmailService.send_contact_email(
            full_name=request.full_name,
            email=request.email,
            phone=request.phone,
            service=request.service,
            message=request.message
        )

        # Send confirmation email to contact
        try:
            EmailService.send_confirmation_email(
                recipient_email=request.email,
                full_name=request.full_name
            )
        except Exception as e:
            logger.warning(f"Failed to send confirmation email: {str(e)}")
            # Don't fail the request if confirmation email fails

        return {
            "status": "success",
            "message": "Contact form submitted successfully",
            "message_id": response["MessageId"]
        }

    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process contact form"
        )