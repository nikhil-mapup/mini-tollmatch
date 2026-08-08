from collections import defaultdict

from models.gps import GPSRecord


class GroupByUnitProcessor:

    def process(self, records: list[GPSRecord]) -> dict[int, list[GPSRecord]]:
        grouped = defaultdict(list)

        for record in records:
            grouped[record.unit].append(record)

        return dict(grouped)