from models.gps_gap import GPSGap


class GPSGapRepository:

    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("unit", 1), ("previous_timestamp", 1)])

    def save(self, gap: GPSGap):
        self.collection.insert_one(gap.model_dump(mode="json"))

    def update_missed_toll_flag(self, gap: GPSGap):
        """Matches on the same natural key the gap was originally saved with."""
        self.collection.update_one(
            {
                "unit": gap.unit,
                "previous_timestamp": gap.previous_timestamp.isoformat(),
                "next_timestamp": gap.next_timestamp.isoformat(),
            },
            {"$set": {
                "possible_missed_toll": gap.possible_missed_toll,
                "matched_toll_point_name": gap.matched_toll_point_name,
            }},
        )