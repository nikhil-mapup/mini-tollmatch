class TripPointRepository:
    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("trip_id", 1), ("timestamp", 1)])

    def insert_points(self, trip):
        # Re-running reconstruction should not duplicate points.
        self.collection.delete_many({"trip_id": trip.trip_id})

        documents = [
            {
                "trip_id": trip.trip_id,
                "unit": trip.unit,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "timestamp": point.gps_timestamp,
            }
            for point in trip.gps_points
        ]
        if documents:
            self.collection.insert_many(documents, ordered=False)
