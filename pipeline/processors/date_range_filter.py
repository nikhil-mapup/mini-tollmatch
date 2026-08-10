from datetime import datetime


class DateRangeFilter:
    

    def __init__(self, start: datetime | None, end: datetime | None):
        self.start = start
        self.end = end

    def filter_gps(self, records: list) -> list:
        return [r for r in records if self._in_range(r.gps_timestamp)]

    def filter_invoices(self, records: list) -> list:
        return [r for r in records if self._in_range(r.entry_time)]

    def _in_range(self, ts: datetime) -> bool:
        if self.start and ts < self.start:
            return False
        if self.end and ts > self.end:
            return False
        return True