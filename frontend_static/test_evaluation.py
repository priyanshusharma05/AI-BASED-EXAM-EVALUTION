
import sys
import os
from pathlib import Path
import json

# Add the evaluation model directory to Python path
EVALUATION_DIR = Path("Final_Model_Descriptive").resolve()
sys.path.insert(0, str(EVALUATION_DIR))

# Add backend to path to import models
sys.path.insert(0, str(Path("backend").resolve()))

try:
    from backend.models.evaluation_service import evaluate_answers
    print("✅ Imported evaluate_answers")
    
    # Mock data
    model_answers = {
        "questions": [
            {
                "question_number": "1",
                "total_marks": 10,
                "subparts": [{"id": "a", "question": "Q", "model_answer": "A", "marks": 10}]
            }
        ]
    }
    student_answers = {
        "1": {"a": "A"}
    }
    
    print("Testing evaluate_answers...")
    report = evaluate_answers(model_answers, student_answers)
    print("✅ Evaluation successful!")
    print(json.dumps(report, indent=2))
    
except Exception as e:
    print(f"❌ Evaluation failed: {e}")
    import traceback
    traceback.print_exc()
