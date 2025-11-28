
import sys
import os
from pathlib import Path

# Add the evaluation model directory to Python path
EVALUATION_DIR = Path("Final_Model_Descriptive").resolve()
sys.path.insert(0, str(EVALUATION_DIR))

print(f"Testing import from {EVALUATION_DIR}")

try:
    import integrated_evaluation
    print("✅ Import successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
