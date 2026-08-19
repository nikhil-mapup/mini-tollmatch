from datetime import timedelta
from config.config import (
    ROUTE_STITCH_MAX_GAP_MINUTES,
    ROUTE_STITCH_MAX_DISTANCE_KM,
    TRIP_BREAK_DWELL_MINUTES,
)
from models.route_segment import RouteSegment
from models.trip import PhysicalTrip
from utils.geo import haversine_distance_km
from processors.route_trip_stats import TripBuildStats


class RouteStitcher:
    def __init__(self, max_gap_minutes: int = ROUTE_STITCH_MAX_GAP_MINUTES, max_distance_km: float = ROUTE_STITCH_MAX_DISTANCE_KM, trip_break_dwell_minutes: int = TRIP_BREAK_DWELL_MINUTES,):
        self.max_gap = timedelta(minutes=max_gap_minutes)
        self.max_distance_km = max_distance_km
        self.trip_break_dwell_minutes = trip_break_dwell_minutes
        

    def process(self, unit: str, segments: list[RouteSegment], stats: TripBuildStats | None = None) -> list[PhysicalTrip]:
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
            if previous.boundary_reason == "gps_gap":

                can_stitch = False

            # A dwell is different from a GPS outage.
            elif previous.boundary_reason == "dwell":

                dwell_minutes = (
                    previous.boundary_duration_minutes
                )

                can_stitch = (
                    dwell_minutes is not None
                    and dwell_minutes < self.trip_break_dwell_minutes
                    and distance <= self.max_distance_km
                )

            else:

                can_stitch = (
                    time_gap <= self.max_gap
                    and distance <= self.max_distance_km
                )

            if can_stitch:
                current_segments.append(segment)
            else:
                if stats:

                    if time_gap > self.max_gap:
                        stats.stitch_rejections_time += 1

                    if distance > self.max_distance_km:
                        stats.stitch_rejections_distance += 1

                    stats.largest_stitch_distance_km = max(
                        stats.largest_stitch_distance_km,
                        distance,
                    )
                trips.append(self._create_trip(unit=unit, segments=current_segments))
                current_segments = [segment]

        # Final trip
        trips.append(self._create_trip(unit=unit, segments=current_segments))
        if stats:
            stats.trips += len(trips)
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