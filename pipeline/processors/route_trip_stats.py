from dataclasses import dataclass


@dataclass
class TripBuildStats:
    gps_points: int = 0
    trips: int = 0
    units: int = 0
    segments: int = 0
    time_gap_splits: int = 0
    dwell_splits: int = 0
    stitch_rejections_time: int = 0
    stitch_rejections_distance: int = 0
    dwell_trip_breaks: int = 0
    dwell_stitches: int = 0
    largest_gap_minutes: float = 0.0
    largest_stitch_distance_km: float = 0.0
