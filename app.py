from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["exam_system"]
users = db["users"]
exams = db["exams"]

@app.route("/")
def home():
    return "Flask backend for AI Exam Evaluation System is running!"

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if users.find_one({"email": data["email"]}):
        return jsonify({"error": "User already exists"}), 400
    users.insert_one({
        "fullname": data["fullname"],
        "email": data["email"],
        "password": data["password"],
        "role": data["role"]
    })
    return jsonify({"message": "Signup successful"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user = users.find_one({"email": data["email"], "password": data["password"], "role": data["role"]})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"message": "Login successful", "name": user["fullname"]}), 200

@app.route("/api/exams", methods=["GET"])
def get_exams():
    exam_list = list(exams.find({}, {"_id": 0}))
    return jsonify({"exams": exam_list})

# File upload placeholders
@app.route("/api/upload-key", methods=["POST"])
def upload_key():
    return jsonify({"message": "Answer key uploaded successfully!"})

@app.route("/api/upload-sheet", methods=["POST"])
def upload_sheet():
    return jsonify({"message": "Answer sheet uploaded successfully!"})

@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    return jsonify({"result": "Evaluation completed successfully!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
