from datetime import timedelta

from config.config import (
    GPS_GAP_THRESHOLD_MINUTES,
    DWELL_RADIUS_KM,
    DWELL_THRESHOLD_MINUTES,
)
from models.gps import GPSRecord
from models.gps_gap import GPSGap
from models.route_segment import RouteSegment
from utils.geo import haversine_distance_km
from processors.route_trip_stats import TripBuildStats

class RouteSegmenter:

    def __init__(
        self,
        gap_threshold_minutes: int = GPS_GAP_THRESHOLD_MINUTES,
        dwell_radius_km: float = DWELL_RADIUS_KM,
        dwell_threshold_minutes: int = DWELL_THRESHOLD_MINUTES,
    ):
        self.gap_threshold = timedelta(minutes=gap_threshold_minutes)
        self.dwell_radius_km = dwell_radius_km
        self.dwell_threshold_minutes = timedelta(minutes=dwell_threshold_minutes)
        self.dwell_15_30 = 0
        self.dwell_30_60 = 0
        self.dwell_60_120 = 0
        self.dwell_120_240 = 0
        self.dwell_240_plus = 0

        self.dwell_durations = []

    def process(self, unit: str, records: list[GPSRecord], stats: TripBuildStats | None = None) -> tuple[list[RouteSegment], list[GPSGap]]:
        if not records:
            return [], []

        records = sorted(records, key=lambda record: record.gps_timestamp)

        segments: list[RouteSegment] = []
        gaps: list[GPSGap] = []

        current_points: list[GPSRecord] = []
        route_number = 1

        i = 0
        n = len(records)
        previous_record = None

        while i < n:
            record = records[i]

            if previous_record is None:
                current_points.append(record)
                previous_record = record
                i += 1
                continue

            # --- Signal 1: time gap (device went silent) ---
            gap = record.gps_timestamp - previous_record.gps_timestamp
            
            if gap > self.gap_threshold:
                if stats:
                    stats.time_gap_splits += 1

                    gap_minutes = gap.total_seconds() / 60
                    stats.largest_gap_minutes = max(
                        stats.largest_gap_minutes,
                        gap_minutes,
                    )
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
                if current_points:
                    segments.append(self._create_segment(unit=unit, points=current_points, route_number=route_number, boundary_reason="gps_gap"))
                    route_number += 1
                current_points = [record]
                previous_record = record
                i += 1
                continue

            # --- Signal 2: dwell (device kept reporting, vehicle stopped moving) ---
            dwell_result = self._find_dwell_end(
                records,
                i,
            )

            if dwell_result is not None:

                dwell_end_index, dwell_duration_minutes = dwell_result

                if stats:
                    stats.dwell_splits += 1

                self.dwell_durations.append(dwell_duration_minutes)
                if dwell_duration_minutes < 30:
                    self.dwell_15_30 += 1
                elif dwell_duration_minutes < 60:
                    self.dwell_30_60 += 1
                elif dwell_duration_minutes < 120:
                    self.dwell_60_120 += 1
                elif dwell_duration_minutes < 240:
                    self.dwell_120_240 += 1
                else:
                    self.dwell_240_plus += 1

                # Keep the dwell GPS points in the current segment.
                dwell_points = records[i:dwell_end_index + 1]

                current_points.extend(dwell_points)

                if current_points:
                    segments.append(
                        self._create_segment(
                            unit=unit,
                            points=current_points,
                            route_number=route_number,
                            boundary_reason="dwell",
                            boundary_duration_minutes=dwell_duration_minutes,
                        )
                    )

                    route_number += 1

                current_points = []

                i = dwell_end_index + 1
                previous_record = None

                continue

            current_points.append(record)
            previous_record = record
            i += 1

        if current_points:
            segments.append(self._create_segment(unit=unit, points=current_points, route_number=route_number))
            
        if stats:
            stats.segments += len(segments)

        return segments, gaps

    def _find_dwell_end(
        self,
        records: list[GPSRecord],
        start_index: int,
    ) -> tuple[int, float] | None:

        anchor = records[start_index]
        j = start_index

        while j + 1 < len(records):

            candidate = records[j + 1]

            distance = haversine_distance_km(
                anchor.latitude,
                anchor.longitude,
                candidate.latitude,
                candidate.longitude,
            )

            if distance > self.dwell_radius_km:
                break

            j += 1

        if j == start_index:
            return None

        duration = (
            records[j].gps_timestamp
            - anchor.gps_timestamp
        )

        if duration >= self.dwell_threshold_minutes:

            duration_minutes = (
                duration.total_seconds() / 60
            )

            return j, duration_minutes

        return None

    def _create_segment(self, unit: str, points: list[GPSRecord], route_number: int, boundary_reason: str | None = None, boundary_duration_minutes: float | None = None,) -> RouteSegment:
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
            boundary_reason=boundary_reason,
            boundary_duration_minutes=boundary_duration_minutes,
        )
