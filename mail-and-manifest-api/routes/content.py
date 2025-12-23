import logging
from typing import Optional

from fastapi import HTTPException, UploadFile, File, Form, Depends, status

from ._router import router
from .models import Images, Image
from shared.db.models import ImageItem
from shared.s3.models import S3Storage
from security.api_key import verify_api_key

logger = logging.getLogger(__name__)

@router.get("/images")
async def get_images() -> dict:
    """
    Get all images endpoint with public URLs.

    Returns:
        dict: List of all images with their public S3 URLs
    """
    try:
        items = ImageItem.get_all_images()

        # Add public URLs to each image
        images_with_urls = []
        for item in items:
            image_data = {
                **item,
                "url": S3Storage.get_public_url(item["s3_path"])
            }
            images_with_urls.append(image_data)

        return {
            "images": images_with_urls
        }
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch images"
        )

@router.get("/image/{image_id}")
async def get_image(image_id: str) -> dict:
    """
    Get a single image by ID.

    Args:
        image_id: UUID of image to retrieve

    Returns:
        dict: Image record with presigned URL
    """
    try:
        image_record = ImageItem.get_image(image_id)
        if not image_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Generate public S3 URL
        url = S3Storage.get_public_url(image_record["s3_path"])

        return {
            "status": "success",
            "image": Image(**image_record),
            "url": url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch image"
        )

@router.post("/image", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def upload_image(
    file: UploadFile = File(...),
    description: str = Form(...),
    tags: str = Form(...)
) -> dict:
    """
    Upload image endpoint (requires admin authentication).

    Args:
        file: Image file to upload
        description: Image description
        tags: Comma-separated list of tags (e.g., "featured,doors")

    Returns:
        dict: Created image record with presigned URL
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )

        # Parse tags from comma-separated string
        tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]

        if not tag_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one tag is required"
            )

        # Read file content
        contents = await file.read()

        # Upload to S3
        s3_path = S3Storage.upload_image(
            file_content=contents,
            filename=file.filename or "image.jpg",
            content_type=file.content_type
        )

        # Create database record
        image_record = ImageItem.create_image(
            s3_path=s3_path,
            description=description,
            tags=tag_list
        )

        # Generate public S3 URL for immediate access
        url = S3Storage.get_public_url(s3_path)

        return {
            "status": "success",
            "message": "Image uploaded successfully",
            "image": Image(**image_record),
            "url": url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )

@router.put("/image/{image_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
async def update_image(
    image_id: str,
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
) -> dict:
    """
    Update image metadata (requires admin authentication).

    Args:
        image_id: UUID of image to update
        description: New description (optional)
        tags: New comma-separated tags (optional)

    Returns:
        dict: Updated image record
    """
    try:
        # Verify image exists
        existing = ImageItem.get_image(image_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Parse tags if provided
        tag_list = None
        if tags is not None:
            tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
            if not tag_list:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="If tags are provided, at least one tag is required"
                )

        # Update image
        updated_image = ImageItem.update_image(
            image_id=image_id,
            description=description,
            tags=tag_list
        )

        return {
            "status": "success",
            "message": "Image updated successfully",
            "image": Image(**updated_image)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update image"
        )

@router.delete("/image/{image_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
async def delete_image(image_id: str) -> dict:
    """
    Delete image endpoint (requires admin authentication).

    Args:
        image_id: UUID of image to delete

    Returns:
        dict: Success response
    """
    try:
        # Get image record to find S3 path
        image_record = ImageItem.get_image(image_id)
        if not image_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        # Delete from S3
        S3Storage.delete_image(image_record["s3_path"])

        # Delete from database
        ImageItem.delete_image(image_id)

        return {
            "status": "success",
            "message": "Image deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        )