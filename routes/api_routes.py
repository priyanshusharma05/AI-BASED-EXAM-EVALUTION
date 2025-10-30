import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from database import users, exams, submissions, results
from models.evaluation_model import evaluate_answer_text


ALLOWED_EXT = set(['png', 'jpg', 'jpeg', 'pdf', 'txt'])


api_bp = Blueprint('api', __name__)




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT




@api_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')


    if users.find_one({'email': email}):
        return jsonify({'error': 'User already exists'}), 400


    user = {'name': name, 'email': email, 'password': password, 'role': role}
    res = users.insert_one(user)
    user['_id'] = str(res.inserted_id)
    return jsonify({'message': 'User created', 'user': {'email': email, 'name': name, 'role': role}})

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')


    user = users.find_one({'email': email})
    if not user or user.get('password') != password:
        return jsonify({'error': 'Invalid credentials'}), 401


    # Return minimal user object; in production use JWT or session
    return jsonify({'message': 'Logged in', 'user': {'email': user['email'], 'name': user.get('name'), 'role': user.get('role')}})


@api_bp.route('/upload_answer_key', methods=['POST'])
def upload_answer_key():
# teacher uploads an answer key (text file or image/pdf) for an exam
    exam_title = request.form.get('title') or f"Exam-{uuid.uuid4().hex[:6]}"
    description = request.form.get('description', '')


    file = request.files.get('file')
    filename = None
    if file and allowed_file(file.filename):
        fname = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{fname}"
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(path)


    exam = {'title': exam_title, 'description': description, 'answer_key_file': filename}
    res = exams.insert_one(exam)
    exam['_id'] = str(res.inserted_id)
    return jsonify({'message': 'Answer key uploaded', 'exam_id': exam['_id']})


@api_bp.route('/exams', methods=['GET'])
def list_exams():
    docs = list(exams.find({}))
    for d in docs:
        d['id'] = str(d.get('_id'))
        d.pop('_id', None)
    return jsonify({'exams': docs})

@api_bp.route('/upload_submission', methods=['POST'])
def upload_submission():
    # student submits files (images/PDF) or text answer
    exam_id = request.form.get('exam_id')
    student_email = request.form.get('email')
    student_name = request.form.get('name', '')
    text_answer = request.form.get('text_answer')


    file = request.files.get('file')
    filename = None
    if file and allowed_file(file.filename):
        fname = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{fname}"
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(path)


    submission = {
        'exam_id': exam_id,
        'student_email': student_email,
        'student_name': student_name,
        'file': filename,
        'text_answer': text_answer,
        'status': 'uploaded'
    }
    res = submissions.insert_one(submission)
    submission_id = str(res.inserted_id)
    return jsonify({'message': 'Submission received', 'submission_id': submission_id})

@api_bp.route('/evaluate/<submission_id>', methods=['POST'])
def evaluate_submission(submission_id):
    sub = submissions.find_one({'_id': __import__('bson').ObjectId(submission_id)})
    if not sub:
        return jsonify({'error': 'Submission not found'}), 404


    exam = exams.find_one({'_id': __import__('bson').ObjectId(sub.get('exam_id'))}) if sub.get('exam_id') else None
    # For this stub, assume answer key is stored as plain text file on disk
    answer_key_text = request.json.get('answer_key_text') if request.is_json else ''


    # If answer_key_file is present and no text provided, try to read text file (only if .txt)
    if not answer_key_text and exam and exam.get('answer_key_file') and exam['answer_key_file'].endswith('.txt'):
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], exam['answer_key_file'])
        try:
            with open(path, 'r', encoding='utf-8') as f:
                answer_key_text = f.read()
        except Exception:
            answer_key_text = ''


    # Decide student_text: use text_answer if present. For images/pdf you'd plug OCR here.
    student_text = sub.get('text_answer') or ''


    # EVALUATION: call the evaluation model (stub)
    eval_result = evaluate_answer_text(student_text, answer_key_text)


    result_doc = {
        'submission_id': submission_id,
        'exam_id': sub.get('exam_id'),
        'student_email': sub.get('student_email'),
        'score': eval_result['score'],
        'ratio': eval_result['ratio'],
        'feedback': eval_result['feedback']
    }
    results.insert_one(result_doc)


    # update submission
    submissions.update_one({'_id': __import__('bson').ObjectId(submission_id)}, {'$set': {'status': 'evaluated'}})


    return jsonify({'message': 'Evaluated', 'result': result_doc})




@api_bp.route('/results/<submission_id>', methods=['GET'])
def get_result(submission_id):
    r = results.find_one({'submission_id': submission_id})
    if not r:
        return jsonify({'error': 'Result not found'}), 404
    r['id'] = str(r.get('_id'))
    r.pop('_id', None)
    return jsonify({'result': r})




@api_bp.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    # serve uploaded files (for preview). In production, use proper static hosting / signed URLs
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)