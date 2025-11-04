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
# FOLDER CONFIGURATION
# ==============================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
KEY_FOLDER = os.path.join(UPLOAD_FOLDER, "keys")
ANSWER_FOLDER = os.path.join(UPLOAD_FOLDER, "answers")
DESCRIPTIVE_FOLDER = os.path.join(ANSWER_FOLDER, "descriptive")
OMR_FOLDER = os.path.join(ANSWER_FOLDER, "omr")

for folder in [KEY_FOLDER, DESCRIPTIVE_FOLDER, OMR_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


# ==============================
# HELPERS
# ==============================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_url(folder, subfolder, filename):
    """Return a consistent URL for uploaded files"""
    return f"http://127.0.0.1:5000/uploads/{folder}/{subfolder}/{filename}"


# ==============================
# ROUTES
# ==============================
@app.route("/")
def home():
    return "✅ Flask backend for AI Evaluator is running!"


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
    return jsonify({"message": "Signup successful ✅"}), 201


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
        return jsonify({"error": "Invalid credentials ❌"}), 401

    redirect_url = (
        "http://127.0.0.1:5500/teacher-dashboard.html"
        if user["role"] == "teacher"
        else "http://127.0.0.1:5500/student-dashboard.html"
    )

    return jsonify({
        "message": f"Welcome, {user['fullname']} ✅",
        "redirect": redirect_url
    }), 200


# ---------- TEACHER UPLOAD ----------
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
            "file_url": f"http://127.0.0.1:5000/uploads/keys/{filename}",
            "timestamp": datetime.datetime.now().isoformat()
        })
        return jsonify({"message": "Answer key uploaded successfully ✅"}), 201

    return jsonify({"error": "Invalid file type"}), 400


# ---------- STUDENT UPLOAD ----------
@app.route("/api/upload-answer", methods=["POST"])
def upload_answer():
    if not request.files.getlist("files"):
        return jsonify({"error": "No files uploaded"}), 400

    exam_name = request.form.get("exam_name", "").strip()
    subject = request.form.get("subject", "").strip()
    roll_number = request.form.get("roll_number", "").strip()
    notes = request.form.get("notes", "").strip()
    sheet_type = request.form.get("answer_sheet_type", "Descriptive").strip().lower()
    student_email = request.form.get("student", "Unknown Student")

    if not (exam_name and subject and roll_number):
        return jsonify({"error": "All required fields must be filled"}), 400

    folder_path = OMR_FOLDER if sheet_type == "omr" else DESCRIPTIVE_FOLDER
    os.makedirs(folder_path, exist_ok=True)

    uploaded_files = request.files.getlist("files")
    saved_files, file_urls = [], []

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(folder_path, filename)
            file.save(save_path)
            saved_files.append(filename)
            file_urls.append(get_file_url("answers", sheet_type, filename))

    if not saved_files:
        return jsonify({"error": "No valid files uploaded"}), 400

    record = {
        "type": "answer_sheet",
        "exam_name": exam_name,
        "subject": subject,
        "roll_number": roll_number,
        "notes": notes,
        "answer_sheet_type": sheet_type,
        "student": student_email,
        "files": saved_files,
        "file_urls": file_urls,
        "status": "pending",
        "timestamp": datetime.datetime.now().isoformat()
    }
    uploads.insert_one(record)
    return jsonify({
        "message": f"{len(saved_files)} file(s) uploaded successfully ✅",
        "data": record
    }), 201


# ---------- STUDENT DASHBOARD FETCH ----------
@app.route("/api/get-student-submissions", methods=["GET"])
def get_student_submissions():
    roll_number = request.args.get("roll_number", "").strip()
    student_email = request.args.get("student", "").strip()

    query = {"type": "answer_sheet"}
    if roll_number:
        query["roll_number"] = roll_number
    if student_email:
        query["student"] = student_email

    submissions = list(uploads.find(query, {"_id": 0}))
    submissions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify({"submissions": submissions}), 200


# ---------- TEACHER VIEW ----------
@app.route("/api/student-submissions", methods=["GET"])
def get_all_student_submissions():
    submissions = list(uploads.find({"type": "answer_sheet"}, {"_id": 0}))
    submissions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify({"submissions": submissions}), 200


# ---------- TEACHER: FETCH ALL PENDING ANSWERS ----------
@app.route("/api/pending-answers", methods=["GET"])
def get_pending_answers():
    """Return all answer sheets pending evaluation"""
    submissions = list(uploads.find({"type": "answer_sheet", "status": "pending"}, {"_id": 0}))
    submissions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return jsonify({"pending": submissions}), 200


# ---------- TEACHER: START AI EVALUATION (Mock for now) ----------
@app.route("/api/start-evaluation/<roll_number>", methods=["POST"])
def start_evaluation(roll_number):
    """Mock AI Evaluation (to be replaced with ML model later)"""
    submission = uploads.find_one({"roll_number": roll_number, "status": "pending"})
    if not submission:
        return jsonify({"error": "Submission not found or already evaluated"}), 404

    # ⚙️ Mock Evaluation (replace this with your ML model later)
    marks = 60 + (hash(roll_number) % 40)  # pseudo-random score
    feedback = "Good effort! Improve handwriting and conceptual explanations."

    uploads.update_one(
        {"roll_number": roll_number},
        {"$set": {
            "status": "evaluated",
            "marks_obtained": marks,
            "total_marks": 100,
            "feedback": feedback,
            "evaluated_on": datetime.datetime.now().isoformat()
        }}
    )

    return jsonify({
        "message": f"✅ Evaluation complete for Roll No {roll_number}",
        "marks_obtained": marks,
        "feedback": feedback
    }), 200


# ---------- TEACHER MANUAL EVALUATION ----------
@app.route("/api/evaluate-submission", methods=["POST"])
def evaluate_submission():
    """Allows teacher to manually mark a student's submission as evaluated"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No evaluation data received"}), 400

    roll_number = data.get("roll_number")
    exam_name = data.get("exam_name")
    marks_obtained = data.get("marks_obtained")
    total_marks = data.get("total_marks", 100)
    feedback = data.get("feedback", "")

    if not (roll_number and exam_name and marks_obtained is not None):
        return jsonify({"error": "Missing required fields"}), 400

    result = uploads.update_one(
        {"roll_number": roll_number, "exam_name": exam_name},
        {"$set": {
            "status": "evaluated",
            "marks_obtained": marks_obtained,
            "total_marks": total_marks,
            "feedback": feedback,
            "evaluated_on": datetime.datetime.now().isoformat()
        }}
    )

    if result.matched_count == 0:
        return jsonify({"error": "No matching submission found"}), 404

    return jsonify({"message": "✅ Submission evaluated successfully"}), 200


# ---------- SERVE FILES ----------
@app.route("/uploads/<path:filepath>")
def serve_file(filepath):
    """Serve uploaded files dynamically regardless of nesting depth"""
    safe_path = os.path.abspath(os.path.join(app.config["UPLOAD_FOLDER"], filepath))

    # Prevent directory traversal
    if not safe_path.startswith(os.path.abspath(app.config["UPLOAD_FOLDER"])):
        return jsonify({"error": "Unauthorized file access attempt"}), 403

    if not os.path.exists(safe_path):
        return jsonify({"error": f"File not found: {filepath}"}), 404

    directory = os.path.dirname(safe_path)
    filename = os.path.basename(safe_path)
    return send_from_directory(directory, filename)

# ---------- DASHBOARD STATS ----------
@app.route("/api/dashboard-stats", methods=["GET"])
def dashboard_stats():
    """Return overall stats for teacher dashboard"""
    try:
        total_exams = uploads.count_documents({"type": "answer_key"})
        total_submissions = uploads.count_documents({"type": "answer_sheet"})
        evaluated = uploads.count_documents({"type": "answer_sheet", "status": "evaluated"})
        pending = uploads.count_documents({"type": "answer_sheet", "status": "pending"})

        return jsonify({
            "total_exams": total_exams,
            "total_submissions": total_submissions,
            "evaluated": evaluated,
            "pending": pending
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
