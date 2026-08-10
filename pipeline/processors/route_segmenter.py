from datetime import timedelta

from config.config import GPS_GAP_THRESHOLD_MINUTES
from models.gps import GPSRecord
from models.gps_gap import GPSGap
from models.route_segment import RouteSegment


class RouteSegmenter:
    def __init__(self, gap_threshold_minutes: int = GPS_GAP_THRESHOLD_MINUTES):
        self.gap_threshold = timedelta(minutes=gap_threshold_minutes)

    def process(self, unit: str, records: list[GPSRecord]) -> tuple[list[RouteSegment], list[GPSGap]]:
        if not records:
            return [], []

        records = sorted(records, key=lambda record: record.gps_timestamp)

        segments = []
        gaps = []

        current_points = []
        route_number = 1

        previous_record = None
        for record in records:
            if previous_record is None:
                current_points.append(record)
                previous_record = record
                continue

            gap = record.gps_timestamp - previous_record.gps_timestamp
            if gap > self.gap_threshold:
                gaps.append(GPSGap(
                    unit=unit,
                    previous_timestamp=previous_record.gps_timestamp,
                    next_timestamp=record.gps_timestamp,
                    previous_latitude=previous_record.latitude,
                    previous_longitude=previous_record.longitude,
                    next_latitude=record.latitude,
                    next_longitude=record.longitude,
                    gap_seconds=gap.total_seconds(),
                    threshold_seconds=self.gap_threshold.total_seconds(),
                    route_split=True,
                ))
                segments.append(self._create_segment(unit=unit,points=current_points,route_number=route_number))
                route_number += 1
                current_points = []

            current_points.append(record)
            previous_record = record

        # Final segment
        if current_points:
            segments.append(self._create_segment(unit=unit, points=current_points, route_number=route_number))

        return segments, gaps

    def _create_segment(self, unit: str, points: list[GPSRecord], route_number: int) -> RouteSegment:
        return RouteSegment(
            route_id=(
                f"ROUTE-{unit}-{route_number:04d}"
            ),
            unit=unit,
            start_time=points[0].gps_timestamp,
            end_time=points[-1].gps_timestamp,
            start_latitude=points[0].latitude,
            start_longitude=points[0].longitude,
            end_latitude=points[-1].latitude,
            end_longitude=points[-1].longitude,
            gps_point_count=len(points),
            gps_points=points,
        )