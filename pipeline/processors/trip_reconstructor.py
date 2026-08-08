from datetime import timedelta
from config.config import TRIP_GAP_THRESHOLD_MINUTES
from models.gps import GPSRecord
from models.trip import Trip

class TripReconstructor:
    def __init__(self, gap_threshold_minutes: int = TRIP_GAP_THRESHOLD_MINUTES):
        self.gap_threshold = timedelta(minutes=gap_threshold_minutes)

    def reconstruct(self, unit: int, records: list[GPSRecord]) -> list[Trip]:
        if not records:
            return []

        records = sorted(records, key=lambda record: record.gps_timestamp)

        trips: list[Trip] = []

        current_trip_points: list[GPSRecord] = []
        trip_number = 1
        previous_record = None

        for record in records:
            if previous_record is None:
                current_trip_points.append(record)
                previous_record = record
                continue

            gap = record.gps_timestamp - previous_record.gps_timestamp

            if gap > self.gap_threshold:
                trips.append(self._create_trip(unit=unit, points=current_trip_points, trip_number=trip_number))
                trip_number += 1
                current_trip_points = []

            current_trip_points.append(record)
            previous_record = record

        # Add final trip
        if current_trip_points:
            trips.append(self._create_trip(unit=unit, points=current_trip_points, trip_number=trip_number))

        print(f"Trips: {trips}")
        return trips

    def _create_trip(self, unit: int, points: list[GPSRecord], trip_number: int) -> Trip:
        return Trip(
            trip_id=f"TRIP-{unit}-{trip_number:04d}",
            unit=unit,
            start_time=points[0].gps_timestamp,
            end_time=points[-1].gps_timestamp,
            gps_point_count=len(points),
            gps_points=points,
        )