import os
import logging
from typing import Optional
from textwrap import dedent

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# SES Configuration from environment
SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL", "noreply@onpointgaragedoors.com")
RECIPIENT_EMAIL = os.getenv("SES_RECIPIENT_EMAIL", "info@onpointgaragedoors.com")

# Initialize SES client
ses_client = boto3.client("ses")


def send_contact_email(
    full_name: str,
    email: str,
    phone: Optional[str],
    service: str,
    message: Optional[str],
) -> dict:
    """
    Send a contact form submission email to On Point Garage Doors via SES.
    """

    phone_text = f"Phone: {phone}\n" if phone else ""
    message_text = f"\nMessage:\n{message}\n" if message else ""

    subject = f"New Contact Form Submission – {service}"

    body_text = dedent(
        f"""
        New contact form submission received:

        Name: {full_name}
        Email: {email}
        {phone_text}Service: {service}
        {message_text}
        ---
        This email was sent from the On Point Garage Doors website contact form.
        """
    )

    body_html = dedent(
        f"""
        <html>
          <body>
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {full_name}</p>
            <p><strong>Email:</strong> {email}</p>
            {f"<p><strong>Phone:</strong> {phone}</p>" if phone else ""}
            <p><strong>Service:</strong> {service}</p>
            {f"<p><strong>Message:</strong><br>{message}</p>" if message else ""}
            <hr>
            <p><em>This email was sent from the On Point Garage Doors website contact form.</em></p>
          </body>
        </html>
        """
    )

    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                "ToAddresses": [RECIPIENT_EMAIL],
            },
            Message={
                "Subject": {
                    "Data": subject,
                    "Charset": "UTF-8",
                },
                "Body": {
                    "Text": {
                        "Data": body_text,
                        "Charset": "UTF-8",
                    },
                    "Html": {
                        "Data": body_html,
                        "Charset": "UTF-8",
                    },
                },
            },
        )

        logger.info(f"Contact email sent successfully: {response['MessageId']}")
        return response

    except ClientError as e:
        logger.error(f"Error sending email: {e.response['Error']['Message']}")
        raise