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


class RouteSegmenter:
    """
    Splits a unit's sorted GPS pings into trip segments using TWO
    independent signals, not one:

      1. TIME GAP — the device stopped transmitting for longer than
         gap_threshold. This is the original check, unchanged: if the
         device goes silent, that's a trip boundary.

      2. DWELL — the device kept transmitting, but the vehicle stopped
         MOVING for longer than dwell_threshold (positions all within
         dwell_radius_km of each other). This is the fix for the bug
         where a full week collapsed into one trip: a device that pings
         every ~60 seconds around the clock, including overnight while
         parked, never produces a time gap large enough to trigger signal
         #1 — but it very clearly produces a long stationary period, which
         signal #2 catches.

    Points inside a qualifying dwell period are excluded from both the
    segment before and after it — they represent the vehicle at rest, not
    part of any trip.
    """

    def __init__(
        self,
        gap_threshold_minutes: int = GPS_GAP_THRESHOLD_MINUTES,
        dwell_radius_km: float = DWELL_RADIUS_KM,
        dwell_threshold_minutes: int = DWELL_THRESHOLD_MINUTES,
    ):
        self.gap_threshold = timedelta(minutes=gap_threshold_minutes)
        self.dwell_radius_km = dwell_radius_km
        self.dwell_threshold = timedelta(minutes=dwell_threshold_minutes)

    def process(self, unit: str, records: list[GPSRecord]) -> tuple[list[RouteSegment], list[GPSGap]]:
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
                    segments.append(self._create_segment(unit=unit, points=current_points, route_number=route_number))
                    route_number += 1
                current_points = [record]
                previous_record = record
                i += 1
                continue

            # --- Signal 2: dwell (device kept reporting, vehicle stopped moving) ---
            dwell_end_index = self._find_dwell_end(records, i)
            if dwell_end_index is not None:
                # Everything gathered so far (up to and including
                # previous_record) is one completed segment — the dwell
                # period itself is excluded entirely, not attached to
                # either side.
                if current_points:
                    segments.append(self._create_segment(unit=unit, points=current_points, route_number=route_number))
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

        return segments, gaps

    def _find_dwell_end(self, records: list[GPSRecord], start_index: int) -> int | None:
        """
        Scans forward from start_index while each point stays within
        dwell_radius_km of the anchor point (records[start_index]).
        Returns the index of the last point in that stationary run IF the
        elapsed time across the run meets dwell_threshold — otherwise
        returns None (not a qualifying dwell, e.g. a brief traffic stop).
        """
        anchor = records[start_index]
        j = start_index

        while j + 1 < len(records):
            candidate = records[j + 1]
            distance = haversine_distance_km(
                anchor.latitude, anchor.longitude,
                candidate.latitude, candidate.longitude,
            )
            if distance > self.dwell_radius_km:
                break
            j += 1

        if j == start_index:
            return None

        duration = records[j].gps_timestamp - anchor.gps_timestamp
        if duration >= self.dwell_threshold:
            return j
        return None

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
