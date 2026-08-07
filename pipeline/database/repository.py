class MongoRepository:
    def __init__(self, collection):
        self.collection = collection

    def insert_many(self, docs):
        if docs:
            self.collection.insert_many(docs)

    def insert_one(self, doc):
        self.collection.insert_one(doc)

    def find(self, query=None):
        return list(self.collection.find(query or {}))

    def delete_all(self):
        self.collection.delete_many({})