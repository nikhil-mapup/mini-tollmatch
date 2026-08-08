from datetime import datetime

from pydantic import BaseModel


class GPSGap(BaseModel):

    unit: int

    previous_timestamp: datetime

    next_timestamp: datetime

    gap_seconds: float

    threshold_seconds: float

    route_split: bool