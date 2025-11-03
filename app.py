from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ==============================
# DATABASE SETUP
# ==============================
client = MongoClient("mongodb://localhost:27017/")
db = client["exam_system"]
users = db["users"]
exams = db["exams"]
uploads = db["uploads"]

# ==============================
# UPLOAD FOLDER CONFIG
# ==============================
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "keys"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "answers"), exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


# ==============================
# HELPER FUNCTION
# ==============================
def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ==============================
# ROUTES
# ==============================
@app.route("/")
def home():
    return "✅ Flask backend for AI Exam Evaluation System is running!"


# ---------- SIGNUP ----------
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    if users.find_one({"email": data["email"]}):
        return jsonify({"error": "User already exists"}), 400

    users.insert_one({
        "fullname": data["fullname"],
        "email": data["email"],
        "password": data["password"],
        "role": data["role"]
    })
    return jsonify({
        "message": "Signup successful ✅",
        "redirect": "http://127.0.0.1:5500/login.html"
    }), 201


# ---------- LOGIN ----------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    user = users.find_one({
        "email": data["email"],
        "password": data["password"],
        "role": data["role"]
    })

    if not user:
        return jsonify({"error": "Invalid email, password, or role ❌"}), 401

    # Redirect based on role
    if user["role"] == "teacher":
        redirect_url = "http://127.0.0.1:5500/teacher-dashboard.html"
    else:
        redirect_url = "http://127.0.0.1:5500/student-dashboard.html"

    return jsonify({
        "message": f"Welcome back, {user['fullname']}! ✅",
        "redirect": redirect_url
    }), 200


# ---------- TEACHER UPLOAD ANSWER KEY ----------
@app.route("/api/upload-key", methods=["POST"])
def upload_key():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    teacher = request.form.get("teacher", "Unknown Teacher")

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], "keys", filename)
        file.save(save_path)

        uploads.insert_one({
            "type": "answer_key",
            "uploaded_by": teacher,
            "filename": filename,
            "path": save_path
        })

        return jsonify({"message": "Answer key uploaded successfully ✅"}), 201

    return jsonify({"error": "Invalid file type"}), 400


# ---------- STUDENT UPLOAD ANSWER SHEET ----------
@app.route("/api/upload-answer", methods=["POST"])
def upload_answer():
    """Handle student answer sheet uploads"""
    if "files[]" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    # Form fields
    exam_name = request.form.get("exam_name")
    subject = request.form.get("subject")
    roll_number = request.form.get("roll_number")
    notes = request.form.get("notes", "")

    uploaded_files = request.files.getlist("files[]")
    saved_files = []

    upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], "answers")
    os.makedirs(upload_dir, exist_ok=True)

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)
            saved_files.append(filename)

    # Save record to MongoDB
    uploads.insert_one({
        "type": "answer_sheet",
        "exam_name": exam_name,
        "subject": subject,
        "roll_number": roll_number,
        "notes": notes,
        "files": saved_files
    })

    return jsonify({
        "message": f"{len(saved_files)} answer sheet(s) uploaded successfully ✅",
        "files": saved_files
    }), 201


# ---------- EVALUATION ----------
@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    return jsonify({"result": "Evaluation complete ✅"}), 200


# ---------- FETCH EXAMS ----------
@app.route("/api/exams", methods=["GET"])
def get_exams():
    exam_list = list(exams.find({}, {"_id": 0}))
    return jsonify({"exams": exam_list})


# ---------- SERVE UPLOADED FILES ----------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
