import logging
from typing import Optional

from fastapi import HTTPException, status, Depends

from ._router import router
from .models import Manifest, Image
from shared.db.models import ImageItem
from security.api_key import verify_api_key

logger = logging.getLogger(__name__)

@router.get("/manifest", response_model=Manifest)
async def get_manifest() -> Manifest:
    """
    Get manifest endpoint - returns images grouped by category.

    Returns:
        Manifest: Images organized by category (featured, doors, openers, gates, custom)
    """
    try:
        # Get all images from database
        items = ImageItem.get_all_images()

        # Organize images by tags
        featured = []
        doors = []
        openers = []
        gates = []
        custom = []

        for item in items:
            image = Image(**item)
            tags = item.get("tags", [])

            if "featured" in tags:
                featured.append(image)
            if "door" in tags or "doors" in tags:
                doors.append(image)
            if "opener" in tags or "openers" in tags:
                openers.append(image)
            if "gate" in tags or "gates" in tags:
                gates.append(image)
            if "custom" in tags:
                custom.append(image)

        return Manifest(
            featured=featured,
            doors=doors,
            openers=openers,
            gates=gates,
            custom=custom
        )

    except Exception as e:
        logger.error(f"Error fetching manifest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch manifest"
        )

@router.put("/manifest/{image_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
async def update_manifest_image(
    image_id: str,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None
) -> dict:
    """
    Update manifest image endpoint (requires admin authentication).

    Args:
        image_id: UUID of image to update
        description: New description (optional)
        tags: New tags list (optional)

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

        # Update image
        updated_image = ImageItem.update_image(
            image_id=image_id,
            description=description,
            tags=tags
        )

        return {
            "status": "success",
            "message": "Image updated successfully",
            "image": Image(**updated_image)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating manifest image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update manifest image"
        )

@router.delete("/manifest/{image_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
async def delete_manifest_image(image_id: str) -> dict:
    """
    Delete manifest image endpoint (requires admin authentication).

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

        # Import S3Storage here to avoid circular import
        from shared.s3.models import S3Storage

        # Delete from S3
        S3Storage.delete_image(image_record["s3_path"])

        # Delete from database
        ImageItem.delete_image(image_id)

        return {
            "status": "success",
            "message": "Manifest image deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting manifest image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete manifest image"
        )