from datetime import datetime
from models.gps import GPSRecord

class GPSFilter:
    def __init__(self,units: list[int],start_time: datetime,end_time: datetime):
        print(f"Filtering GPS records for units: {units}, start_time: {start_time}, end_time: {end_time}")
        self.units = set(units)
        self.start_time = start_time
        self.end_time = end_time

    def process(self,records: list[GPSRecord]) -> list[GPSRecord]:
        return [
            record
            for record in records
            if (
                record.unit in self.units
                and self.start_time
                <= record.gps_timestamp
                < self.end_time
            )
        ]