from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Mismatch(BaseModel):
    transaction_id: str
    unit: Optional[str] = None
    trip_id: Optional[str] = None

    # Top-level business outcome:
    # matched | mismatch | unassigned | duplicate | insufficient_gps
    verdict: str

    # Only populated for verdict == "mismatch":
    # misread | unmatched | max_toll
    mismatch_type: Optional[str] = None

    reason_code: Optional[str] = None

    entry_time: datetime
    billing_method: Optional[str] = None

    expected_amount: Optional[float] = None
    billed_amount: float
    delta_amount: Optional[float] = None

    matched_toll_point_name: Optional[str] = None
    time_delta_seconds: Optional[float] = None
    gps_distance_km: Optional[float] = None

    inferred_vehicle_type: Optional[str] = None
    vehicle_type_confidence: Optional[str] = None

    is_duplicate: bool = False

    status: str = "open"
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
