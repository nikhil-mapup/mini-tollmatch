from models.trip import PhysicalTrip


class TripRepository:

    def __init__(self, collection):

        self.collection = collection

        self.collection.create_index(
            [
                ("unit", 1),
                ("start_time", 1),
            ]
        )

    def save(self, trip: PhysicalTrip):

        document = {
            "_id": trip.trip_id,
            "unit": trip.unit,
            "start_time": trip.start_time,
            "end_time": trip.end_time,
            "route_ids": trip.route_ids,
            "gps_point_count": trip.gps_point_count,
        }

        self.collection.replace_one(
            {"_id": trip.trip_id},
            document,
            upsert=True,
        )