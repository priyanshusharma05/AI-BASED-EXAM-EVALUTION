"""
Extraction Service Wrapper
===========================

This module provides a clean interface to the integrated extraction model
for use in FastAPI endpoints. It wraps the functionality from 
Final_Model_Descriptive/Extraction_modelanswers/integrated_extraction.py

Functions:
    - extract_student_answers(pdf_path): Extract answers from student answer sheet
    - extract_question_paper(pdf_path): Extract questions and generate model answers
"""

import os
import sys
import json
from pathlib import Path

# Add the extraction model directory to Python path
EXTRACTION_DIR = Path(__file__).parent.parent / "Final_Model_Descriptive" / "Extraction_modelanswers"
sys.path.insert(0, str(EXTRACTION_DIR))

try:
    from integrated_extraction import (
        extract_answers_from_pdf,
        extract_questions_from_pdf,
        get_api_key
    )
except ImportError as e:
    print(f"⚠️ Warning: Could not import extraction module: {e}")
    extract_answers_from_pdf = None
    extract_questions_from_pdf = None
    get_api_key = None


class ExtractionError(Exception):
    """Custom exception for extraction errors"""
    pass


def extract_student_answers(pdf_path: str) -> dict:
    """
    Extract student answers from a PDF answer sheet.
    
    Args:
        pdf_path: Absolute path to the student answer sheet PDF
        
    Returns:
        Dictionary containing extracted student answers in structured format
        
    Raises:
        ExtractionError: If extraction fails
        FileNotFoundError: If PDF file doesn't exist
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if extract_answers_from_pdf is None:
        raise ExtractionError("Extraction module not available. Check dependencies.")
    
    try:
        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            raise ExtractionError(
                "GEMINI_API_KEY not set in environment variables. "
                "Please set it before using extraction features."
            )
        
        # Extract answers using the integrated extraction model
        result = extract_answers_from_pdf(pdf_path, api_key)
        
        if not result:
            raise ExtractionError("Extraction returned empty result")
        
        return result
        
    except Exception as e:
        raise ExtractionError(f"Failed to extract student answers: {str(e)}")


def extract_question_paper(pdf_path: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Extract questions from a question paper PDF and generate model answers.
    
    Args:
        pdf_path: Absolute path to the question paper PDF
        model: Gemini model name to use (default: gemini-2.5-flash)
        
    Returns:
        Dictionary containing questions with model answers in structured format:
        {
            "questions": [
                {
                    "question_number": "Q1",
                    "total_marks": 10,
                    "attempt_required": "all" or <number>,
                    "selection_policy": "none" or "first_n",
                    "subparts": [
                        {
                            "id": "a",
                            "question": "...",
                            "model_answer": "...",
                            "marks": 5
                        }
                    ]
                }
            ]
        }
        
    Raises:
        ExtractionError: If extraction fails
        FileNotFoundError: If PDF file doesn't exist
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if extract_questions_from_pdf is None:
        raise ExtractionError("Extraction module not available. Check dependencies.")
    
    try:
        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            raise ExtractionError(
                "GEMINI_API_KEY not set in environment variables. "
                "Please set it before using extraction features."
            )
        
        # Extract questions and generate model answers
        print(f"🔹 Requesting extraction with model: {model}")
        result = extract_questions_from_pdf(pdf_path, api_key, model)
        
        if not result:
            raise ExtractionError("Extraction returned empty result")
        
        return result
        
    except Exception as e:
        raise ExtractionError(f"Failed to extract question paper: {str(e)}")


def save_extraction_result(data: dict, output_path: str) -> None:
    """
    Save extraction result to a JSON file.
    
    Args:
        data: Extraction result dictionary
        output_path: Path where to save the JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
