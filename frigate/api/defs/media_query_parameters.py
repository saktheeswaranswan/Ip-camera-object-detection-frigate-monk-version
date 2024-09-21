from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Extension(str, Enum):
    webp = "webp"
    png = "png"
    jpg = "jpg"
    jpeg = "jpeg"


class MediaLatestFrameQueryParams(BaseModel):
    extension: Extension = Extension.webp
    bbox: Optional[int] = None
    timestamp: Optional[int] = None
    zones: Optional[int] = None
    mask: Optional[int] = None
    motion: Optional[int] = None
    regions: Optional[int] = None
    quality: Optional[int] = 70
    height: Optional[int] = None

class MediaEventsSnapshotQueryParams(BaseModel):
    download: bool = False,
    timestamp: Optional[int] = None,
    bbox: Optional[int] = None,
    crop: Optional[int] = None,
    height: Optional[int] = None,
    quality: Optional[int] = 70,
