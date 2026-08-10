from pymongo.errors import BulkWriteError

from models.invoice import InvoiceRecord


class InvoiceRepository:

    def __init__(self, collection):
        self.collection = collection
        # Unique index on transaction_id — first line of defense against
        # duplicate invoice batches being re-ingested. See Layer 1 docs.
        self.collection.create_index([("transaction_id", 1)], unique=True)
        self.collection.create_index([("unit", 1), ("entry_time", 1)])

    def save_many(self, invoices: list[InvoiceRecord]) -> dict:
        if not invoices:
            return {"inserted": 0, "duplicates_rejected": 0}

        documents = [inv.model_dump(mode="json") for inv in invoices]

        inserted = 0
        duplicates_rejected = 0
        try:
            result = self.collection.insert_many(documents, ordered=False)
            inserted = len(result.inserted_ids)
        except BulkWriteError as bwe:
            write_errors = bwe.details.get("writeErrors", [])
            duplicates_rejected = sum(1 for e in write_errors if e.get("code") == 11000)
            inserted = len(documents) - len(write_errors)

        return {"inserted": inserted, "duplicates_rejected": duplicates_rejected}

    def find_by_unit(self, unit: str) -> list[dict]:
        return list(self.collection.find({"unit": unit}).sort("entry_time", 1))
