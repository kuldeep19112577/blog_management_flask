from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

Mongo_url=os.environ["Mongo_url"]

mongo_client=MongoClient(Mongo_url)

database=mongo_client["blog_management"]

users_collection = database["users"]
blog_collection = database["blogs"]
