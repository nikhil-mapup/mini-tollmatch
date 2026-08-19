from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Mismatch(BaseModel):
    
    transaction_id: str
    unit: str
    trip_id: Optional[str] = None  # None when no trip could be matched at all

    verdict: str
    reason_code: Optional[str] = None
    # unassigned | unmatched | duplicate | max_toll | misread | reconciled

    # Copied from the invoice at creation time. Required for date-range
    # filtering to work at all — without this field, every date-filtered
    # query against `mismatches` silently matched zero documents (Mongo
    # drops documents missing the field being compared), which is what
    # produced both the "1/1/1" display bug and the null-breakdown crash.
    entry_time: datetime

    billing_method: Optional[str] = None  # "tag" | "plate" | None
    expected_amount: Optional[float] = None
    billed_amount: float
    delta_amount: Optional[float] = None

    matched_toll_point_name: Optional[str] = None
    time_delta_seconds: Optional[float] = None  # invoice.entry_time vs matched toll's arrival

    status: str = "open"  # open | reconciled
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
