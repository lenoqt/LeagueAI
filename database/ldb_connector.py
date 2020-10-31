from pymongo import MongoClient

class MongoCollection(object):

    def __init__(self, uri='localhost:27017'):
        self.uri = uri
        self.collection = None

    def __enter__(self):
        self.connection = MongoClient(self.uri)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.connection.close()