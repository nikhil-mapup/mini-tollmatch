from processors.group_by_unit import GroupByUnitProcessor
from processors.route_segmenter import RouteSegmenter
from processors.route_stitcher import RouteStitcher


class RouteTripService:

    def __init__(self,route_repository,gap_repository,trip_repository,trip_point_repository):
        self.group_processor = GroupByUnitProcessor()
        self.segmenter = RouteSegmenter()
        self.stitcher = RouteStitcher()
        self.route_repository = route_repository
        self.gap_repository = gap_repository
        self.trip_repository = trip_repository
        self.trip_point_repository = trip_point_repository

    def process(self, gps_records):

        grouped = self.group_processor.process(gps_records)

        all_trips = []

        for unit, records in grouped.items():
            # 1. Create route segments
            segments, gaps = self.segmenter.process(unit=unit,records=records)

            # 2. Persist gaps
            for gap in gaps:
                self.gap_repository.save(gap)

            # 3. Persist route segments
            for segment in segments:
                self.route_repository.save(segment)

            # 4. Stitch route segments
            trips = self.stitcher.process(unit=unit, segments=segments)

            # 5. Persist physical trips
            for trip in trips:
                self.trip_repository.save(trip)
                self.trip_point_repository.insert_points(trip)
                all_trips.append(trip)

        return all_trips