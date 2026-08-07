from datetime import datetime

from pydantic import BaseModel


class GPSRecord(BaseModel):

    latitude: float

    longitude: float

    gps_timestamp: datetime

    unit: str
