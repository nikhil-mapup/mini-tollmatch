from datetime import datetime
from models.gps import GPSRecord

class GPSFilter:
    def __init__(self,units: list[str] | None):
        self.units = set(units) if units else None
        print(f"Filtering GPS records for units: {'ALL' if self.units is None else self.units}")

    def process(self,records: list[GPSRecord]) -> list[GPSRecord]:
        if self.units is None:
            return records
        return [
            record
            for record in records
            if (
                record.unit in self.units
            )
        ]