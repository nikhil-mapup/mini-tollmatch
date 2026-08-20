from models.route_segment import RouteSegment


class RouteRepository:
    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("unit", 1), ("start_time", 1)])

    def save(self, route: RouteSegment):
        document = {
            "_id": route.route_id,
            "unit": route.unit,
            "start_time": route.start_time,
            "end_time": route.end_time,
            "start_latitude": route.start_latitude,
            "start_longitude": route.start_longitude,
            "end_latitude": route.end_latitude,
            "end_longitude": route.end_longitude,
            "gps_point_count": route.gps_point_count,
            "boundary_reason": route.boundary_reason,
            "boundary_duration_minutes": route.boundary_duration_minutes,
        }
        self.collection.replace_one({"_id": route.route_id}, document, upsert=True)
