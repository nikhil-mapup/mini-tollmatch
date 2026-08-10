from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GPSGap(BaseModel):

    unit: str

    previous_timestamp: datetime
    next_timestamp: datetime

    # Coordinates bracketing the gap — needed to check whether this gap
    # sits near a known toll location. Previously this model only stored
    # timestamps, which meant a gap could never be checked against toll
    # geometry at all.
    previous_latitude: float
    previous_longitude: float
    next_latitude: float
    next_longitude: float

    gap_seconds: float
    threshold_seconds: float
    route_split: bool

    # Populated later, once toll locations are known (after Step 2 runs) —
    # a gap is never silently discarded, only flagged if it correlates
    # with a known toll's coordinates.
    possible_missed_toll: bool = False
    matched_toll_point_name: Optional[str] = None