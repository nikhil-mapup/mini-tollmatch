from pymongo import MongoClient
from config.config import MONGO_URI, DATABASE_NAME


class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]

    def collection(self, name: str):
        return self.db[name]