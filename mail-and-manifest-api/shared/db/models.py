import os
import logging
from typing import Optional
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# DynamoDB Table Name from environment
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "opgd-images-content")

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME) # type: ignore


class ImageItem:
    """DynamoDB interface for Images & Static Content"""

    @staticmethod
    def create_image(
        s3_path: str,
        description: str,
        tags: list[str]
    ) -> dict:
        """
        Create a new image record in DynamoDB.

        Args:
            s3_path: S3 object path
            description: Image description
            tags: List of tags for categorization

        Returns:
            dict: Created image item
        """
        image_id = str(uuid4())

        item = {
            "uuid": image_id,
            "s3_path": s3_path,
            "description": description,
            "tags": tags
        }

        try:
            table.put_item(Item=item)
            logger.info(f"Created image record: {image_id}")
            return item
        except ClientError as e:
            logger.error(f"Error creating image: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def get_image(image_id: str) -> Optional[dict]:
        """
        Get an image record by UUID.

        Args:
            image_id: Image UUID

        Returns:
            Optional[dict]: Image item or None if not found
        """
        try:
            response = table.get_item(Key={"uuid": image_id})
            return response.get("Item")
        except ClientError as e:
            logger.error(f"Error getting image: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def get_all_images() -> list[dict]:
        """
        Get all image records.

        Returns:
            list[dict]: List of all image items
        """
        try:
            response = table.scan()
            items = response.get("Items", [])

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items.extend(response.get("Items", []))

            logger.info(f"Retrieved {len(items)} images")
            return items
        except ClientError as e:
            logger.error(f"Error scanning images: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def get_images_by_tag(tag: str) -> list[dict]:
        """
        Get images by a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            list[dict]: List of image items with the specified tag
        """
        try:
            response = table.scan(
                FilterExpression=Attr("tags").contains(tag)
            )
            items = response.get("Items", [])

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                    FilterExpression=Attr("tags").contains(tag)
                )
                items.extend(response.get("Items", []))

            logger.info(f"Retrieved {len(items)} images with tag '{tag}'")
            return items
        except ClientError as e:
            logger.error(f"Error querying images by tag: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def update_image(
        image_id: str,
        s3_path: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> dict:
        """
        Update an image record.

        Args:
            image_id: Image UUID
            s3_path: New S3 path (optional)
            description: New description (optional)
            tags: New tags list (optional)

        Returns:
            dict: Updated image item
        """
        update_expression = []
        expression_values = {}
        expression_names = {}

        if s3_path is not None:
            update_expression.append("#s = :s")
            expression_values[":s"] = s3_path
            expression_names["#s"] = "s3_path"

        if description is not None:
            update_expression.append("#d = :d")
            expression_values[":d"] = description
            expression_names["#d"] = "description"

        if tags is not None:
            update_expression.append("#t = :t")
            expression_values[":t"] = tags
            expression_names["#t"] = "tags"

        if not update_expression:
            logger.warning(f"No fields to update for image {image_id}")
            return ImageItem.get_image(image_id)

        try:
            response = table.update_item(
                Key={"uuid": image_id},
                UpdateExpression="SET " + ", ".join(update_expression),
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names,
                ReturnValues="ALL_NEW"
            )
            logger.info(f"Updated image record: {image_id}")
            return response["Attributes"]
        except ClientError as e:
            logger.error(f"Error updating image: {e.response['Error']['Message']}")
            raise

    @staticmethod
    def delete_image(image_id: str) -> bool:
        """
        Delete an image record.

        Args:
            image_id: Image UUID

        Returns:
            bool: True if deleted successfully
        """
        try:
            table.delete_item(Key={"uuid": image_id})
            logger.info(f"Deleted image record: {image_id}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting image: {e.response['Error']['Message']}")
            raise
