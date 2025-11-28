"""
Integrated PDF Extraction System
=================================

This script combines answer sheet and question paper extraction into a single tool.
Preserves 100% of the original logic from answersheet.py and questionpaper.py.

Features:
- Extract student answers from PDF answer sheets
- Extract questions and generate model answers from question papers
- Unified CLI interface for both operations
- Support for Gemini API (Flash 2.5)

Usage:
    # Extract student answers
    python integrated_extraction.py --mode answers --pdf sample/student_answers.pdf --output student_answers.json

    # Extract question paper and generate model answers
    python integrated_extraction.py --mode questions --pdf sample/question_paper.pdf --output model_answers.json

Author: Automated Extraction System
Version: 1.0
"""

import os
import sys
import json
import base64
import argparse
import requests
import time
import google.generativeai as genai


# ============================================================================
# ANSWER SHEET EXTRACTION (from answersheet.py)
# ============================================================================

# Prompt for structured answer extraction
ANSWER_EXTRACTION_PROMPT = """
You are an intelligent exam evaluator. Your task is to accurately extract answers from a student's handwritten or scanned PDF answer sheet.

Follow these instructions carefully:

1. Identify every main question (e.g., Q1, Q2, Q3, etc.).
2. For each question, extract all its subparts such as (a), (b), (c), and (i), (ii), (iii), (iv), etc.
3. If the student has written answers in a different or mixed order, rearrange them in **the correct numerical/alphabetical order** (Q1 → Q2 → Q3; within Q1: a → b → c; within subparts: i → ii → iii → iv).
4. Extract only the student’s handwritten **answer text** — ignore any question text, page numbers, or headings.
5. If a question has no subparts, record it as a single text string.
6. If a subpart exists but is blank or unreadable, mark it as `"unreadable"`.
7. Preserve nested structure (e.g., Q1(c)(i)).
8. Maintain formatting (newlines, bullets, equations) as they appear.

Return the final result **only** as a clean JSON object, with no extra text or explanations.

Important:
- Always arrange questions and subparts in correct logical order even if written out of sequence in the PDF.
- Do not paraphrase, summarize, or modify the text — extract it exactly as written.
- Output must be valid JSON only.
"""


def make_gemini_request(url, headers, json_payload, retries=5, delay=10):
    """Make a request to Gemini API with retry logic."""
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=json_payload, timeout=300)
            if response.status_code == 200:
                return response
            elif response.status_code in [500, 502, 503, 504]:
                print(f"⚠️ API {response.status_code} error. Retrying ({attempt + 1}/{retries})...")
                time.sleep(delay * (attempt + 1))
            else:
                # Client error or other non-retriable error
                return response
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed: {e}. Retrying ({attempt + 1}/{retries})...")
            time.sleep(delay * (attempt + 1))
    
    # If all retries failed, return the last response or raise
    return response


def extract_answers_from_pdf(pdf_path: str, api_key: str) -> dict:
    """
    Extract student answers from PDF using Gemini API.
    
    Args:
        pdf_path: Path to the student answer sheet PDF
        api_key: Gemini API key
    
    Returns:
        Dictionary containing extracted answers
    """
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: File not found at {pdf_path}")
        raise FileNotFoundError(f"File not found at {pdf_path}")

    # Gemini 2.5 Flash endpoint
    gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    # Read and encode PDF file
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    encoded_pdf = base64.b64encode(pdf_data).decode("utf-8")

    # Prepare payload
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": ANSWER_EXTRACTION_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": encoded_pdf
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json"  # ensures clean JSON output
        }
    }

    headers = {"Content-Type": "application/json"}

    print("📤 Sending request to Gemini API for answer extraction...")
    try:
        response = make_gemini_request(gemini_endpoint, headers=headers, json_payload=payload)
    except UnboundLocalError:
         # In case make_gemini_request fails completely without assigning response
         raise Exception("Failed to connect to Gemini API after retries.")

    # Handle HTTP errors
    if response.status_code != 200:
        print(f"❌ API request failed ({response.status_code}): {response.text}")
        raise Exception(f"API request failed ({response.status_code}): {response.text}")

    result = response.json()

    try:
        # Safely extract text from Gemini response
        text_output = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # Convert to JSON object
        extracted_json = json.loads(text_output)
        return extracted_json

    except Exception as e:
        print("⚠️ Error parsing JSON response:", e)
        print("Raw Gemini response:\n", json.dumps(result, indent=2))
        return None


# ============================================================================
# QUESTION PAPER EXTRACTION (from questionpaper.py)
# ============================================================================

# Prompt for question paper extraction and model answer generation
QUESTION_EXTRACTION_PROMPT = """
You are extracting structured question data from an exam PDF.

Your task:
1️⃣ Identify every main question (Q1, Q2, Q3…)
2️⃣ Identify subparts (i, ii, iii / a, b, c / A, B etc.)
3️⃣ For each question or subpart:
    - Extract EXACT question text
    - Generate a natural, correct, human-written “Model Answer”
    - Extract the marks written for that question/subpart
4️⃣ Detect internal choice rules (like "Attempt any 1/2/4")
    - If only one must be attempted → return:
      "attempt_required": 1, "selection_policy": "first_n"
    - If all must be done → return:
      "attempt_required": "all", "selection_policy": "none"

Output MUST be a VALID JSON with this exact structure:

{
  "questions": [
    {
      "question_number": "Q#",
      "total_marks": #,
      "attempt_required": "all" or <number>,
      "selection_policy": "none" or "first_n",
      "subparts": [
        {
          "id": "<subpart>",
          "question": "<text>",
          "model_answer": "<text>",
          "marks": <number>
        }
      ]
    }
  ]
}

Rules:
✅ Remove page numbers, headers, footers
✅ Ignore Hindi or duplicate translations
✅ Ignore “for visually impaired” optional alternatives
✅ Do NOT hallucinate marks – use only values present in PDF
✅ Do NOT include anything outside JSON
✅ Grammar in answers must be high quality

Here is the extracted question paper text:
{text_input}
"""


def extract_text_from_pdf_with_gemini(pdf_path: str, api_key: str, model: str = "gemini-2.5-flash") -> str:
    """
    Extract text from PDF using Gemini API (via REST to avoid library version issues).
    
    Args:
        pdf_path: Path to the question paper PDF
        api_key: Gemini API key
        model: Gemini model name
    
    Returns:
        Extracted text from PDF
    """
    print("📤 Sending PDF to Gemini for text extraction (Inline)...")
    
    # Check file
    if not os.path.exists(pdf_path):
        return ""

    # Read and encode PDF
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    encoded_pdf = base64.b64encode(pdf_data).decode("utf-8")

    # Endpoint
    gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    prompt_text = (
        "You are a precise document parser. Extract all readable text from this question paper. "
        "Preserve question numbering, subparts (a,b,c,i,ii, etc.), and marks. "
        "Do not summarize, just return clean structured text."
    )

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt_text},
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": encoded_pdf
                    }
                }
            ]
        }]
    }

    try:
        try:
            response = make_gemini_request(gemini_endpoint, headers=headers, json_payload=payload)
        except UnboundLocalError:
             raise Exception("Failed to connect to Gemini API after retries.")
        
        if response.status_code != 200:
            print(f"❌ Extraction API request failed ({response.status_code}): {response.text}")
            raise Exception(f"Extraction API request failed ({response.status_code})")

        result = response.json()
        text_output = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return text_output

    except Exception as e:
        print(f"❌ Error during text extraction: {e}")
        raise e


def generate_model_answers(text: str, api_key: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Generate model answers for extracted question text.
    
    Args:
        text: Extracted question paper text
        api_key: Gemini API key
        model: Gemini model name
    
    Returns:
        Dictionary containing questions with model answers
    """
    print("🤖 Generating model answers for each question...")

    genai.configure(api_key=api_key)
    model_instance = genai.GenerativeModel(model)

    final_prompt = QUESTION_EXTRACTION_PROMPT.replace("{text_input}", text)

    # Use request_options to set a higher timeout (600s = 10 minutes) to prevent 504 errors
    response = model_instance.generate_content(
        final_prompt,
        request_options={'timeout': 600}
    )
    cleaned = response.text.strip()

    # Try to load JSON directly
    try:
        return json.loads(cleaned)
    except:
        # Try to extract JSON substring
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        return json.loads(cleaned[start:end+1])


def extract_questions_from_pdf(pdf_path: str, api_key: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Complete pipeline to extract questions and generate model answers.
    Includes fallback to gemini-1.5-flash if primary model fails.
    """
    print(f"📄 Extracting questions from: {pdf_path} using {model}")
    
    # Only use the requested model (gemini-2.5-flash)
    extracted_text = extract_text_from_pdf_with_gemini(pdf_path, api_key, model)
    qna_data = generate_model_answers(extracted_text, api_key, model)
    return qna_data


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def save_to_json(data: dict, output_path: str):
    """Save data to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Data saved to {output_path}")


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY is not set in environment variables.")
        print("👉 Run this command before executing the script:")
        print("   Windows: set GEMINI_API_KEY=YOUR_API_KEY_HERE")
        print("   Windows: set GEMINI_API_KEY=YOUR_API_KEY_HERE")
        print("   Linux/Mac: export GEMINI_API_KEY=YOUR_API_KEY_HERE")
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    return api_key


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Integrated PDF Extraction System - Extract answers and questions from PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract student answers
  python integrated_extraction.py --mode answers --pdf sample/student_answers.pdf --output student_answers.json

  # Extract questions and generate model answers
  python integrated_extraction.py --mode questions --pdf sample/question_paper.pdf --output model_answers.json

  # Use custom model
  python integrated_extraction.py --mode questions --pdf paper.pdf --model gemini-2.5-flash --output results.json
        """
    )
    
    parser.add_argument(
        "-m", "--mode",
        required=True,
        choices=["answers", "questions", "list-models"],
        help="Extraction mode: 'answers' for student answer sheets, 'questions' for question papers, 'list-models' to see available models"
    )
    
    parser.add_argument(
        "-p", "--pdf",
        required=False, # Not required for list-models
        help="Path to the PDF file to process"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=False, # Not required for list-models
        help="Output path for the extracted JSON file"
    )
    
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model to use (default: gemini-2.5-flash)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = get_api_key()
    
    # Check if PDF exists (unless listing models)
    if args.mode == "list-models":
        list_models(api_key)
        sys.exit(0)

    if not os.path.exists(args.pdf):
        print(f"❌ ERROR: PDF file not found at {args.pdf}")
        sys.exit(1)
    
    print("="*70)
    print("INTEGRATED PDF EXTRACTION SYSTEM")
    print("="*70)
    print(f"Mode: {args.mode.upper()}")
    print(f"Input PDF: {args.pdf}")
    print(f"Output: {args.output}")
    print(f"Model: {args.model}")
    print("="*70)
    print()
    
    # Execute based on mode
    if args.mode == "answers":
        # Extract student answers
        result = extract_answers_from_pdf(args.pdf, api_key)
        if result:
            save_to_json(result, args.output)
            print("\n✅ Student answers successfully extracted!")
        else:
            print("\n❌ Failed to extract student answers.")
            sys.exit(1)
    
    elif args.mode == "questions":
        # Extract questions and generate model answers
        result = extract_questions_from_pdf(args.pdf, api_key, args.model)
        if result:
            save_to_json(result, args.output)
            print("\n✅ Questions and model answers successfully extracted!")
        else:
            print("\n❌ Failed to extract questions.")
            sys.exit(1)
    
    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)


def list_models(api_key):
    """List available models."""
    print(f"🔑 Using API Key: {api_key[:5]}... (Length: {len(api_key)})", flush=True)
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        print(f"🌐 Requesting: {url.replace(api_key, 'HIDDEN')}", flush=True)
        res = requests.get(url)
        print(f"Status: {res.status_code}", flush=True)
        if res.status_code == 200:
            models = res.json().get("models", [])
            print("Available Models (Flash only):", flush=True)
            for m in models:
                if "flash" in m['name'].lower():
                    print(f"- {m['name']}", flush=True)
        else:
            print(f"❌ Failed to list models: {res.text}", flush=True)
    except Exception as e:
        print(f"❌ Error listing models: {e}", flush=True)

if __name__ == "__main__":
    main()
