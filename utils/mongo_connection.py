from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json

with open("config.json", "r") as file:
    config = json.load(file)
    
class MongoConnection:
    _instance = None
    _client = None
    _db = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if MongoConnection._client is None:
            uri = config["db_token"]
            MongoConnection._client = MongoClient(uri, server_api=ServerApi('1'))
            MongoConnection._db = MongoConnection._client["Main"]

    def get_collection(self, collection_name: str):
        return MongoConnection._db[collection_name]

    def get_db(self):
        return MongoConnection._db
    
    def get_client(self):
        return MongoConnection._client