from models.gps_gap import GPSGap


class GPSGapRepository:

    def __init__(self, collection):

        self.collection = collection

        self.collection.create_index(
            [
                ("unit", 1),
                ("previous_timestamp", 1),
            ]
        )

    def save(self, gap: GPSGap):

        self.collection.insert_one(
            gap.model_dump()
        )