import json
from Testing.extract_text import extract_text_from_pdf
from Testing.compare_answers import evaluate_answers

student_pdf = "sample/student_answers.pdf"
question_pdf = "sample/question_paper.pdf"

print("🔹 Extracting student answers...")
student_json = extract_text_from_pdf(student_pdf)

print("🔹 Extracting question paper...")
question_json = extract_text_from_pdf(question_pdf)

print("🔹 Evaluating answers...")
evaluation = evaluate_answers(student_json, question_json)

with open("evaluation_result.json", "w", encoding="utf-8") as f:
    f.write(evaluation)

print("✅ Evaluation complete. Saved to evaluation_result.json")
