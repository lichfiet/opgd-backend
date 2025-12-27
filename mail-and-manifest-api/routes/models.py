from typing import Optional
from pydantic import BaseModel

#
# Contact Request
#
class ContactRequest(BaseModel):
    full_name: str
    email: str
    phone: Optional[str]
    service: str
    message: Optional[str]

#
# Manifests & Images
#
class ImageUpload(BaseModel):
    tags: list[str]
    image_file: str
    description: str

class Image(BaseModel):
    uuid: str
    tags: list[str]
    s3_path: str
    description: str
    url: Optional[str] = None

class Images(BaseModel):
    images: list[Image]

class Manifest(BaseModel):
    featured: list[Image]
    doorInstall: list[Image]
    openers: list[Image]
    gates: list[Image]
    customWork: list[Image]
