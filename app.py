from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["exam_system"]
users = db["users"]
exams = db["exams"]
uploads = db["uploads"]

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


@app.route("/api/upload-key", methods=["POST"])
def upload_key():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    teacher = request.form.get("teacher")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        uploads.insert_one({
            "type": "answer_key",
            "uploaded_by": teacher,
            "filename": filename,
            "path": save_path
        })

        return jsonify({"message": "Answer key uploaded successfully!"}), 201

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/api/upload-sheet", methods=["POST"])
def upload_sheet():
    if "files[]" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    student = request.form.get("student")
    uploaded_files = request.files.getlist("files[]")
    saved_files = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            saved_files.append(filename)

    uploads.insert_one({
        "type": "answer_sheet",
        "uploaded_by": student,
        "files": saved_files
    })

    return jsonify({"message": f"{len(saved_files)} file(s) uploaded successfully!"}), 201


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    # Placeholder for AI logic
    return jsonify({"result": "Evaluation complete!"}), 200


@app.route("/api/exams", methods=["GET"])
def get_exams():
    exam_list = list(exams.find({}, {"_id": 0}))
    return jsonify({"exams": exam_list})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
