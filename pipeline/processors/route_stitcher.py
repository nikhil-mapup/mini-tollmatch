from datetime import timedelta

from config.config import (
    ROUTE_STITCH_MAX_GAP_MINUTES,
    ROUTE_STITCH_MAX_DISTANCE_KM,
)

from models.route_segment import RouteSegment
from models.trip import PhysicalTrip

from utils.geo import haversine_distance_km


class RouteStitcher:

    def __init__(self, max_gap_minutes: int = ROUTE_STITCH_MAX_GAP_MINUTES, max_distance_km: float = ROUTE_STITCH_MAX_DISTANCE_KM):
        self.max_gap = timedelta(minutes=max_gap_minutes)
        self.max_distance_km = max_distance_km

    def process(self, unit: str, segments: list[RouteSegment]) -> list[PhysicalTrip]:
        if not segments:
            return []

        segments = sorted(segments, key=lambda segment: segment.start_time)
        trips = []
        current_segments = [segments[0]]

        for segment in segments[1:]:
            previous = current_segments[-1]
            time_gap = segment.start_time - previous.end_time
            distance = haversine_distance_km(
                previous.end_latitude,
                previous.end_longitude,
                segment.start_latitude,
                segment.start_longitude,
            )
            can_stitch = time_gap <= self.max_gap and distance <= self.max_distance_km

            if can_stitch:
                current_segments.append(segment)
            else:
                trips.append(self._create_trip(unit=unit, segments=current_segments))
                current_segments = [segment]

        # Final trip
        trips.append(self._create_trip(unit=unit, segments=current_segments))
        return trips

    def _create_trip(self, unit: str, segments: list[RouteSegment]) -> PhysicalTrip:
        points = []
        for segment in segments:
            points.extend(segment.gps_points)

        return PhysicalTrip(
            trip_id=(
                f"TRIP-{unit}-{segments[0].route_id}"
            ),
            unit=unit,
            start_time=segments[0].start_time,
            end_time=segments[-1].end_time,
            route_ids=[
                segment.route_id
                for segment in segments
            ],
            gps_point_count=len(points),
            gps_points=points,
        )