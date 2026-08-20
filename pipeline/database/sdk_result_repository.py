from models.sdk_result import SDKResult


class SDKResultRepository:
    def __init__(self, collection):
        self.collection = collection

        # Old versions used a unique trip_id index, which prevents storing
        # 2/3/4/5 axle results for the same physical trip.
        try:
            self.collection.drop_index("trip_id_1")
        except Exception:
            pass

        self.collection.create_index(
            [("trip_id", 1), ("requested_vehicle_type", 1)],
            unique=True,
        )
        self.collection.create_index([("unit", 1)])

    @staticmethod
    def _key(trip_id: str, vehicle_type: str) -> str:
        return f"{trip_id}_{vehicle_type}"

    def save(self, result: SDKResult):
        document = result.model_dump(mode="python")
        document["_id"] = self._key(
            result.trip_id,
            result.requested_vehicle_type,
        )
        self.collection.replace_one(
            {"_id": document["_id"]},
            document,
            upsert=True,
        )

    def find_all(self) -> list[SDKResult]:
        results = []
        for document in self.collection.find({}):
            document.pop("_id", None)
            results.append(SDKResult.model_validate(document))
        return results
