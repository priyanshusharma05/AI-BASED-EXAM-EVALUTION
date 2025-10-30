import os
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()


MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'ai_exam_evaluator')


client = MongoClient(MONGO_URI)
db = client[DB_NAME]


users = db.users
exams = db.exams
submissions = db.submissions
results = db.results