import csv
from datetime import timezone
from pathlib import Path

from models.trip import PhysicalTrip

class TripCSVExporter:
    HEADERS = [
        "latitude",
        "longitude",
        "timestamp",
        "units",
    ]

    def export(self, trip: PhysicalTrip, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = (output_dir/ f"{trip.trip_id}.csv")

        with file_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.HEADERS)
            writer.writeheader()
            for point in trip.gps_points:
                timestamp = (
                    point.gps_timestamp.astimezone(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
                writer.writerow(
                    {
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "timestamp": timestamp,
                        "units": point.unit,
                    }
                )

        return file_path
