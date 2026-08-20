from processors.group_by_unit import GroupByUnitProcessor
from processors.route_segmenter import RouteSegmenter
from processors.route_stitcher import RouteStitcher
from processors.route_trip_stats import TripBuildStats

class RouteTripService:
    def __init__(self, route_repository, gap_repository, trip_repository, trip_point_repository):
        self.group_processor = GroupByUnitProcessor()
        self.segmenter = RouteSegmenter()
        self.stitcher = RouteStitcher()
        self.route_repository = route_repository
        self.gap_repository = gap_repository
        self.trip_repository = trip_repository
        self.trip_point_repository = trip_point_repository

    def process(self, gps_records, stats: TripBuildStats | None = None,):
        grouped = self.group_processor.process(gps_records)
        if stats:
            stats.gps_points = len(gps_records)

        all_trips = []
        all_gaps = []  

        if stats:
            stats.units = len(grouped)

        for unit, records in grouped.items():
            segments, gaps = self.segmenter.process(unit=unit, records=records, stats=stats)

            for gap in gaps:
                self.gap_repository.save(gap)
            all_gaps.extend(gaps)

            for segment in segments:
                self.route_repository.save(segment)

            trips = self.stitcher.process(unit=unit, segments=segments, stats=stats)

            for trip in trips:
                self.trip_repository.save(trip)
                # self.trip_point_repository.insert_points(trip)
                all_trips.append(trip)

        return all_trips, all_gaps