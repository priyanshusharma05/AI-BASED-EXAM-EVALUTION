import os
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()

# Prefer the env var name MONGODB_URI but accept legacy MONGO_URI
MONGODB_URI = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/'
# Default DB name aligns with FastAPI app expectations
DB_NAME = os.environ.get('DB_NAME', 'exam_system')


client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

# Export commonly used collections so other modules import them from here
users = db['users']
exams = db['exams']
uploads = db['uploads']

# Backwards-compatible aliases (some modules used submissions/results)
submissions = uploads
results = db['results']