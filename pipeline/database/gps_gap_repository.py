from models.gps_gap import GPSGap


class GPSGapRepository:

    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("unit", 1), ("previous_timestamp", 1)])

    def save(self, gap: GPSGap):
        self.collection.insert_one(gap.model_dump(mode="python"))

    def update_missed_toll_flag(self, gap: GPSGap):
        """
        Matches on the same natural key the gap was originally saved with.
        Uses the real datetime values directly — previously matched against
        .isoformat() strings, which only worked because save() used to
        store timestamps as strings too (the same bug being fixed here).
        Now that save() stores real BSON dates, matching against a string
        would silently match nothing at all.
        """
        self.collection.update_one(
            {
                "unit": gap.unit,
                "previous_timestamp": gap.previous_timestamp,
                "next_timestamp": gap.next_timestamp,
            },
            {"$set": {
                "possible_missed_toll": gap.possible_missed_toll,
                "matched_toll_point_name": gap.matched_toll_point_name,
            }},
        )