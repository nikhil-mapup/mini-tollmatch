from models.sdk_result import SDKResult


class SDKResultRepository:

    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("trip_id", 1)], unique=True)
        self.collection.create_index([("unit", 1)])

    def save(self, result: SDKResult):
        document = result.model_dump(mode="python")
        document["_id"] = result.trip_id
        self.collection.replace_one({"_id": result.trip_id}, document, upsert=True)
