from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

Mongo_url=os.environ["Mongo_url"]

mongo_client=MongoClient(Mongo_url)

database=mongo_client["blog_management"]

users_collection = database["users"]
blog_collection = database["blogs"]
blog_comments=database["comments"]
blog_likes=database["likes"]

users_collection.create_index(
    [("email", 1)],
    unique=True
)

blog_likes.create_index(
    [("blog_id", 1), ("user_id", 1)],
    unique=True
)
