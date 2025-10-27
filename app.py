from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__, template_folder='ExamPilot', static_folder='ExamPilot', static_url_path='')
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['exampilot']

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB Collections
users_collection = db['users']
exams_collection = db['exams']
submissions_collection = db['submissions']
results_collection = db['results']

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        return User(user)
    return None

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.full_name = user_data['full_name']
        self.role = user_data['role']

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        user_data = users_collection.find_one({'email': email, 'role': role})
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            if role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('fullname')
        role = request.form.get('role')
        if users_collection.find_one({'email': email}):
            flash('Email already exists')
            return redirect(url_for('signup'))
        user_data = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'full_name': full_name,
            'role': role
        }
        users_collection.insert_one(user_data)
        flash('Account created successfully')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    return render_template('student-dashboard.html')

@app.route('/teacher-dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('index'))
    return render_template('teacher-dashboard.html')

# API Routes
@app.route('/api/upload-answer-sheet', methods=['POST'])
@login_required
def upload_answer_sheet():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    exam_name = request.form.get('exam_name')
    subject = request.form.get('subject')
    roll_number = request.form.get('roll_number')
    notes = request.form.get('notes')
    
    exam = exams_collection.find_one({'name': exam_name, 'subject': subject})
    if not exam:
        return jsonify({'error': 'Exam not found'}), 404
    
    files = request.files.getlist('answer_sheet')
    file_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + '_' + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            file_paths.append(file_path)
    
    submission_data = {
        'exam_id': exam['_id'],
        'student_id': ObjectId(current_user.id),
        'roll_number': roll_number,
        'answer_sheet_paths': ','.join(file_paths),
        'notes': notes,
        'submitted_at': datetime.utcnow(),
        'status': 'pending'
    }
    submissions_collection.insert_one(submission_data)
    
    return jsonify({'message': 'Answer sheet uploaded successfully'})

@app.route('/api/upload-answer-key', methods=['POST'])
@login_required
def upload_answer_key():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    exam_name = request.form.get('exam_name')
    subject = request.form.get('subject')
    total_marks = int(request.form.get('total_marks'))
    
    file = request.files.get('answer_key')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        exam_data = {
            'name': exam_name,
            'subject': subject,
            'total_marks': total_marks,
            'teacher_id': ObjectId(current_user.id),
            'answer_key_path': file_path,
            'created_at': datetime.utcnow()
        }
        exams_collection.insert_one(exam_data)
        
        return jsonify({'message': 'Answer key uploaded successfully'})
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/api/evaluate/<submission_id>', methods=['POST'])
@login_required
def evaluate_submission(submission_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    submission = submissions_collection.find_one({'_id': ObjectId(submission_id)})
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    exam = exams_collection.find_one({'_id': submission['exam_id']})
    if not exam:
        return jsonify({'error': 'Exam not found'}), 404
    
    # Mock AI evaluation
    score, feedback, breakdown = mock_ai_evaluation(exam, submission)
    
    result_data = {
        'submission_id': ObjectId(submission_id),
        'score': score,
        'feedback': feedback,
        'question_breakdown': breakdown,
        'evaluated_at': datetime.utcnow()
    }
    results_collection.insert_one(result_data)
    
    submissions_collection.update_one({'_id': ObjectId(submission_id)}, {'$set': {'status': 'evaluated'}})
    
    return jsonify({'message': 'Evaluation completed', 'score': score})

@app.route('/api/submissions')
@login_required
def get_submissions():
    if current_user.role == 'teacher':
        submissions = list(submissions_collection.find({'exam_id': {'$in': [exam['_id'] for exam in exams_collection.find({'teacher_id': ObjectId(current_user.id)})]}}))
    else:
        submissions = list(submissions_collection.find({'student_id': ObjectId(current_user.id)}))
    
    result = []
    for s in submissions:
        exam = exams_collection.find_one({'_id': s['exam_id']})
        exam_name = exam['name'] if exam else 'Unknown'
        score = None
        if s['status'] == 'evaluated':
            result_doc = results_collection.find_one({'submission_id': s['_id']})
            score = result_doc['score'] if result_doc else None
        result.append({
            'id': str(s['_id']),
            'exam_name': exam_name,
            'status': s['status'],
            'submitted_at': s['submitted_at'].isoformat(),
            'score': score
        })
    return jsonify(result)

@app.route('/api/results/<submission_id>')
@login_required
def get_result(submission_id):
    submission = submissions_collection.find_one({'_id': ObjectId(submission_id)})
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    if current_user.role == 'student' and str(submission['student_id']) != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    exam = exams_collection.find_one({'_id': submission['exam_id']})
    if current_user.role == 'teacher' and str(exam['teacher_id']) != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    result = results_collection.find_one({'submission_id': ObjectId(submission_id)})
    if not result:
        return jsonify({'error': 'Result not found'}), 404
    
    return jsonify({
        'score': result['score'],
        'feedback': result['feedback'],
        'breakdown': result['question_breakdown']
    })

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'pdf'}

def mock_ai_evaluation(exam, submission):
    # Simulate AI evaluation - in real app, this would call ML models
    import random
    score = random.randint(60, 100)
    feedback = "Good performance with room for improvement."
    breakdown = "[{'question': '1', 'score': '8/10', 'feedback': 'Correct approach'}, {'question': '2', 'score': '7/10', 'feedback': 'Minor error'}]"
    return score, feedback, breakdown

if __name__ == '__main__':
    app.run(debug=True)
