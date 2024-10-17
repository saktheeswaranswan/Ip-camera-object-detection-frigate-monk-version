from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Json

from frigate.api.defs.severity_enum import SeverityEnum


class ReviewSegmentResponse(BaseModel):
    id: str
    camera: str
    start_time: datetime
    end_time: datetime
    has_been_reviewed: bool
    severity: SeverityEnum
    thumb_path: str
    data: Json


class Last24HoursReview(BaseModel):
    reviewed_alert: int
    reviewed_detection: int
    reviewed_motion: int
    total_alert: int
    total_detection: int
    total_motion: int


class DayReview(BaseModel):
    day: datetime
    reviewed_alert: int
    reviewed_detection: int
    reviewed_motion: int
    total_alert: int
    total_detection: int
    total_motion: int


class ReviewSummaryResponse(BaseModel):
    last24Hours: Last24HoursReview
    root: Dict[str, DayReview]


class ReviewActivityMotionResponse(BaseModel):
    start_time: int
    motion: float
    camera: str


class ReviewActivityAudioResponse(BaseModel):
    start_time: int
    audio: int
