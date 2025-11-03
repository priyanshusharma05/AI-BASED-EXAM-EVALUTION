from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import datetime

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
KEY_FOLDER = os.path.join(UPLOAD_FOLDER, "keys")
ANSWER_FOLDER = os.path.join(UPLOAD_FOLDER, "answers")
DESCRIPTIVE_FOLDER = os.path.join(ANSWER_FOLDER, "Descriptive")
OMR_FOLDER = os.path.join(ANSWER_FOLDER, "OMR")

# Create all directories if they don’t exist
for folder in [KEY_FOLDER, DESCRIPTIVE_FOLDER, OMR_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

# ==============================
# HELPER FUNCTIONS
# ==============================
def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_url(folder, subfolder, filename):
    """Generate accessible file URL"""
    return f"http://127.0.0.1:5000/uploads/{folder}/{subfolder}/{filename}"


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

    redirect_url = (
        "http://127.0.0.1:5500/teacher-dashboard.html"
        if user["role"] == "teacher"
        else "http://127.0.0.1:5500/student-dashboard.html"
    )

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
        save_path = os.path.join(KEY_FOLDER, filename)
        file.save(save_path)

        uploads.insert_one({
            "type": "answer_key",
            "uploaded_by": teacher,
            "filename": filename,
            "path": save_path,
            "file_url": f"http://127.0.0.1:5000/uploads/keys/{filename}",
            "timestamp": datetime.datetime.now().isoformat()
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
    exam_name = request.form.get("exam_name", "Untitled Exam")
    subject = request.form.get("subject", "N/A")
    roll_number = request.form.get("roll_number", "Unknown")
    notes = request.form.get("notes", "")
    sheet_type = request.form.get("answer_sheet_type", "Descriptive")  # NEW FIELD

    # Choose folder based on answer sheet type
    if sheet_type == "OMR":
        folder_path = OMR_FOLDER
    else:
        folder_path = DESCRIPTIVE_FOLDER

    uploaded_files = request.files.getlist("files[]")
    saved_files = []
    file_urls = []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(folder_path, filename)
            file.save(save_path)
            saved_files.append(filename)
            file_urls.append(get_file_url("answers", sheet_type, filename))

    # Save record to MongoDB
    uploads.insert_one({
        "type": "answer_sheet",
        "exam_name": exam_name,
        "subject": subject,
        "roll_number": roll_number,
        "notes": notes,
        "answer_sheet_type": sheet_type,
        "files": saved_files,
        "file_urls": file_urls,
        "timestamp": datetime.datetime.now().isoformat()
    })

    return jsonify({
        "message": f"{len(saved_files)} {sheet_type} answer sheet(s) uploaded successfully ✅",
        "files": saved_files
    }), 201


# ---------- TEACHER VIEW STUDENT SUBMISSIONS ----------
@app.route("/api/student-submissions", methods=["GET"])
def get_student_submissions():
    """Return all student uploads for teacher view"""
    submissions = list(uploads.find({"type": "answer_sheet"}, {"_id": 0}))
    submissions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify({"submissions": submissions}), 200


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
@app.route("/uploads/<folder>/<subfolder>/<filename>")
def uploaded_file(folder, subfolder, filename):
    """Serve uploaded files (answer keys or answer sheets)"""
    folder_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, subfolder)
    return send_from_directory(folder_path, filename)


# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
