from models.mismatch import Mismatch


class MismatchRepository:

    def __init__(self, collection):
        self.collection = collection
        self.collection.create_index([("transaction_id", 1)], unique=True)
        self.collection.create_index([("status", 1)])
        self.collection.create_index([("verdict", 1)])

    def save(self, mismatch: Mismatch):
        document = mismatch.model_dump(mode="python")
        self.collection.replace_one(
            {"transaction_id": mismatch.transaction_id}, document, upsert=True
        )

    def save_many(self, mismatches: list[Mismatch]):
        for m in mismatches:
            self.save(m)
