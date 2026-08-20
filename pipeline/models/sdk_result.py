from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExpectedTollPoint(BaseModel):
    toll_id: Optional[str] = None
    name: Optional[str] = None
    road: Optional[str] = None
    agency: Optional[str] = None
    state: Optional[str] = None

    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    arrival_time: Optional[datetime] = None

    tag_cost: Optional[float] = None
    tag_cost_min: Optional[float] = None
    tag_cost_max: Optional[float] = None
    license_plate_cost: Optional[float] = None
    cash_cost: Optional[float] = None

    sdk_trip_id: Optional[str] = None
    requested_vehicle_type: Optional[str] = None
    response_vehicle_type: Optional[str] = None
    vehicle_type_valid: bool = True


class SDKResult(BaseModel):
    trip_id: str
    unit: str

    requested_vehicle_type: str
    response_vehicle_type: Optional[str] = None
    vehicle_type_mismatch: bool = False

    has_tolls: bool
    distance_km: Optional[float] = None
    warnings: list[str] = Field(default_factory=list)
    toll_points: list[ExpectedTollPoint] = Field(default_factory=list)
