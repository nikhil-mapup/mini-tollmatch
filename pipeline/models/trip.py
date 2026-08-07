from datetime import datetime
from pydantic import BaseModel
from models.gps import GPSRecord

class Trip(BaseModel):
    trip_id: str
    unit: str
    start_time: datetime
    end_time: datetime
    gps_points: list[GPSRecord]
