from pymongo import MongoClient
from config.config import MONGO_URI, DATABASE_NAME
class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]

    def get_collection(self, collection_name):
        return self.db[collection_name]