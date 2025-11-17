import os
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# SES Configuration from environment
SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL", "noreply@onpointgaragedoors.com")
RECIPIENT_EMAIL = os.getenv("SES_RECIPIENT_EMAIL", "info@onpointgaragedoors.com")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize SES client
ses_client = boto3.client("ses", region_name=AWS_REGION)


class EmailService:
    """SES interface for sending emails"""

    @staticmethod
    def send_contact_email(
        full_name: str,
        email: str,
        phone: Optional[str],
        service: str,
        message: Optional[str]
    ) -> dict:
        """
        Send a contact form submission email via SES.

        Args:
            full_name: Contact's full name
            email: Contact's email address
            phone: Contact's phone number (optional)
            service: Service they're interested in
            message: Additional message (optional)

        Returns:
            dict: SES response with MessageId
        """
        # Build email body
        phone_text = f"Phone: {phone}\n" if phone else ""
        message_text = f"\nMessage:\n{message}\n" if message else ""

        subject = f"New Contact Form Submission - {service}"
        body_text = f"""
New contact form submission received:

Name: {full_name}
Email: {email}
{phone_text}Service: {service}
{message_text}
---
This email was sent from the On Point Garage Doors website contact form.
"""

        body_html = f"""
<html>
<head></head>
<body>
  <h2>New Contact Form Submission</h2>
  <p><strong>Name:</strong> {full_name}</p>
  <p><strong>Email:</strong> {email}</p>
  {"<p><strong>Phone:</strong> " + phone + "</p>" if phone else ""}
  <p><strong>Service:</strong> {service}</p>
  {"<p><strong>Message:</strong></p><p>" + message + "</p>" if message else ""}
  <hr>
  <p><em>This email was sent from the On Point Garage Doors website contact form.</em></p>
</body>
</html>
"""

        try:
            response = ses_client.send_email(
                Source=SENDER_EMAIL,
                Destination={
                    "ToAddresses": [RECIPIENT_EMAIL],
                    "ReplyToAddresses": [email]
                },
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8"
                    },
                    "Body": {
                        "Text": {
                            "Data": body_text,
                            "Charset": "UTF-8"
                        },
                        "Html": {
                            "Data": body_html,
                            "Charset": "UTF-8"
                        }
                    }
                }
            )
            logger.info(f"Contact email sent successfully: {response['MessageId']}")
            return response
        except ClientError as e:
            logger.error(f"Error sending email: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def send_confirmation_email(
        recipient_email: str,
        full_name: str
    ) -> dict:
        """
        Send a confirmation email to the contact.

        Args:
            recipient_email: Contact's email address
            full_name: Contact's full name

        Returns:
            dict: SES response with MessageId
        """
        subject = "Thank you for contacting On Point Garage Doors"
        body_text = f"""
Hi {full_name},

Thank you for reaching out to On Point Garage Doors! We've received your message and will get back to you as soon as possible.

We appreciate your interest in our services.

Best regards,
On Point Garage Doors Team
"""

        body_html = f"""
<html>
<head></head>
<body>
  <p>Hi {full_name},</p>
  <p>Thank you for reaching out to <strong>On Point Garage Doors</strong>! We've received your message and will get back to you as soon as possible.</p>
  <p>We appreciate your interest in our services.</p>
  <p>Best regards,<br>
  <strong>On Point Garage Doors Team</strong></p>
</body>
</html>
"""

        try:
            response = ses_client.send_email(
                Source=SENDER_EMAIL,
                Destination={
                    "ToAddresses": [recipient_email]
                },
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8"
                    },
                    "Body": {
                        "Text": {
                            "Data": body_text,
                            "Charset": "UTF-8"
                        },
                        "Html": {
                            "Data": body_html,
                            "Charset": "UTF-8"
                        }
                    }
                }
            )
            logger.info(f"Confirmation email sent to {recipient_email}: {response['MessageId']}")
            return response
        except ClientError as e:
            logger.error(f"Error sending confirmation email: {e.response['Error']['Message']}")
            raise
