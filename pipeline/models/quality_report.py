from datetime import datetime, timezone

from pydantic import BaseModel, Field


class QualityReport(BaseModel):

    run_id: str
    stage: str  # e.g. "gps_validation"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    total_input: int
    total_valid: int
    total_invalid: int

    # error code -> count, e.g. {"NULL_ISLAND_COORDINATES": 4, "FUTURE_TIMESTAMP": 1}
    exclusion_counts: dict[str, int]
