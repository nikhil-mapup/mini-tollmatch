from datetime import datetime

from pydantic import BaseModel

from models.gps import GPSRecord


class PhysicalTrip(BaseModel):

    trip_id: str

    unit: int

    start_time: datetime

    end_time: datetime

    route_ids: list[str]

    gps_point_count: int

    gps_points: list[GPSRecord]