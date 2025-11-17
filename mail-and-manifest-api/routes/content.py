import logging

from fastapi import HTTPException, UploadFile, File, Form, Depends, status

from ._router import router
from .models import Images, Image
from shared.db.models import ImageItem
from shared.s3.models import S3Storage
from shared.auth.middleware import verify_admin_password

logger = logging.getLogger(__name__)

@router.get("/images", response_model=Images)
async def get_images() -> Images:
    """
    Get all images endpoint.

    Returns:
        Images: List of all images
    """
    try:
        items = ImageItem.get_all_images()
        images = [Image(**item) for item in items]
        return Images(images=images)
    except Exception as e:
        logger.error(f"Error fetching images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch images"
        )

@router.post("/image", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_admin_password)])
async def upload_image(
    file: UploadFile = File(...),
    description: str = Form(...),
    tags: list[str] = Form([])
) -> dict:
    """
    Upload image endpoint (requires admin authentication).

    Args:
        file: Image file to upload
        description: Image description
        tags: List of tags for categorization

    Returns:
        dict: Created image record
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
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
            tags=tags
        )

        return {
            "status": "success",
            "message": "Image uploaded successfully",
            "image": Image(**image_record)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )

@router.delete("/image/{image_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_admin_password)])
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