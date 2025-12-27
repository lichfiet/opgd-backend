import logging

from fastapi import HTTPException, status

from ._router import router
from .models import Manifest, Image
from shared.db.models import ImageItem
from shared.s3.models import S3Storage

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
        door_install = []
        openers = []
        gates = []
        custom_work = []

        for item in items:
            # Add public URL to image
            image_data = dict(item)
            image_data["url"] = S3Storage.get_public_url(item["s3_path"])
            image = Image(**image_data)
            tags = item.get("tags", [])

            if "featured" in tags:
                featured.append(image)
            if "door" in tags or "doors" in tags:
                door_install.append(image)
            if "opener" in tags or "openers" in tags:
                openers.append(image)
            if "gate" in tags or "gates" in tags:
                gates.append(image)
            if "custom" in tags:
                custom_work.append(image)

        return Manifest(
            featured=featured,
            doorInstall=door_install,
            openers=openers,
            gates=gates,
            customWork=custom_work
        )

    except Exception as e:
        logger.error(f"Error fetching manifest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch manifest"
        )