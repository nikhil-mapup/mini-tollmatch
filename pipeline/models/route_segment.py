from datetime import datetime

from pydantic import BaseModel

from models.gps import GPSRecord


class RouteSegment(BaseModel):

    route_id: str

    unit: int

    start_time: datetime

    end_time: datetime

    start_latitude: float

    start_longitude: float

    end_latitude: float

    end_longitude: float

    gps_point_count: int

    gps_points: list[GPSRecord]