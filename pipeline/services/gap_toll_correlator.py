from config.config import TOLL_MATCH_DISTANCE_KM
from models.gps_gap import GPSGap
from services.toll_location_index import TollLocationIndex
from utils.geo import haversine_distance_km


class GapTollCorrelator:

    def __init__(self, toll_index: TollLocationIndex, distance_km: float = TOLL_MATCH_DISTANCE_KM):
        self.toll_index = toll_index
        self.distance_km = distance_km

    def correlate(self, gaps: list[GPSGap]) -> list[GPSGap]:
        for gap in gaps:
            match = self._nearest_toll_within_range(gap)
            if match:
                gap.possible_missed_toll = True
                gap.matched_toll_point_name = match.name
        return gaps

    def _nearest_toll_within_range(self, gap: GPSGap):
        candidates = self.toll_index.all_points_for_unit(gap.unit)
        best = None
        for point in candidates:
            if point.start_lat is None or point.start_lng is None:
                continue
            dist_before = haversine_distance_km(
                gap.previous_latitude, gap.previous_longitude, point.start_lat, point.start_lng
            )
            dist_after = haversine_distance_km(
                gap.next_latitude, gap.next_longitude, point.start_lat, point.start_lng
            )
            distance = min(dist_before, dist_after)
            if distance <= self.distance_km:
                if best is None or distance < best["distance"]:
                    best = {"distance": distance, "point": point}
        return best