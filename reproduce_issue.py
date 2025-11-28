
import sys
import os

# Add backend directory to path
sys.path.append(r"d:\Final\backend")

from models.extraction_service import extract_student_answers, ExtractionError

print("Attempting to extract student answers without API key...")

# Create a dummy file to pass the existence check
with open("dummy.pdf", "w") as f:
    f.write("dummy content")

try:
    extract_student_answers("dummy.pdf")
    print("❌ Unexpected success (should have failed)")
except ExtractionError as e:
    print(f"✅ Caught expected ExtractionError: {e}")
except Exception as e:
    print(f"❌ Caught unexpected exception: {type(e).__name__}: {e}")
finally:
    if os.path.exists("dummy.pdf"):
        os.remove("dummy.pdf")
