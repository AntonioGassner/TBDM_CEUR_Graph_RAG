import logging
import os
from pymongo import MongoClient

class Database:

    logging.basicConfig(filename='scraping.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    
    def __init__(self):
        self.client = MongoClient(os.getenv('DATABASE_URL', 'mongodb://localhost:27017/'))
        self.db = self.client[os.getenv('DB_NAME', 'ceur_ws')]
        self.papers_collection = self.db["papers"]
        self.volumes_collection = self.db["volumes"]

    def save_volume(self, volume_dict):
        logging.debug(f"Saving volume {volume_dict["volnr"]} to database")
        return self.volumes_collection.insert_one(volume_dict).inserted_id

    def save_paper(self, paper_dict):
        logging.debug(f"Saving volume {paper_dict["title"]} to database")
        self.papers_collection.insert_one(paper_dict)

    def volume_exists(self, volnr):
        return self.volumes_collection.find_one({"volnr": volnr}) is not None

    def get_volume_id(self, volnr):
        volume = self.volumes_collection.find_one({"volnr": volnr})
        return volume["_id"] if volume else None
