import pymongo


class LAIDBConnectionManager:

    def __init__(self, host:str, port:int):
        self.host = host
        self.port = port
        self.connection = None
        
    def __enter__(self):
        try:
            self.connection = pymongo.MongoClient(
                host=self.host, 
                port=self.port,
                serverSelectionTimeoutMS = 3000
            )
        except pymongo.errors.ServerSelectionTimeoutError as err:
            self.connection = None
            print('pymongo error', err)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
