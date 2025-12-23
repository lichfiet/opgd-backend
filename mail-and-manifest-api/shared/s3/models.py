import os
import logging
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# S3 Bucket Name from environment
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "opgd-images-content-prod")

# Initialize S3 client
s3_client = boto3.client("s3")


class S3Storage:
    """S3 interface for image storage"""

    @staticmethod
    def upload_image(
        file_content: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload an image to S3.

        Args:
            file_content: Binary file content
            filename: Original filename
            content_type: MIME type of the file

        Returns:
            str: S3 object path
        """
        # Generate unique filename
        file_extension = filename.split(".")[-1] if "." in filename else "jpg"
        unique_filename = f"{uuid4()}.{file_extension}"
        s3_key = f"images/{unique_filename}"

        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption="AES256"
            )
            logger.info(f"Uploaded image to S3: {s3_key}")
            return s3_key
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def get_image_url(s3_path: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for an image.

        Args:
            s3_path: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            str: Presigned URL
        """
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": s3_path},
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for: {s3_path}")
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def delete_image(s3_path: str) -> bool:
        """
        Delete an image from S3.

        Args:
            s3_path: S3 object key

        Returns:
            bool: True if deleted successfully
        """
        try:
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_path)
            logger.info(f"Deleted image from S3: {s3_path}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting from S3: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def image_exists(s3_path: str) -> bool:
        """
        Check if an image exists in S3.

        Args:
            s3_path: S3 object key

        Returns:
            bool: True if image exists
        """
        try:
            s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking S3 object: {e.response['Error']['Message']}")
            raise
