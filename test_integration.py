import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_integration():
    print("🔍 Checking for pending answers...")
    try:
        resp = requests.get(f"{BASE_URL}/api/pending-answers")
        if resp.status_code != 200:
            print(f"❌ Failed to get pending answers: {resp.status_code} - {resp.text}")
            return

        data = resp.json()
        pending = data.get("pending", [])
        print(f"✅ Found {len(pending)} pending submissions.")

        if not pending:
            print("⚠️ No pending submissions to evaluate. Please upload an answer sheet first.")
            # Try to find *any* submission to re-evaluate for testing purposes
            print("🔍 Looking for any submission to re-evaluate...")
            resp = requests.get(f"{BASE_URL}/api/student-submissions")
            if resp.status_code == 200:
                subs = resp.json().get("submissions", [])
                if subs:
                    pending = [subs[0]]
                    print(f"✅ Found existing submission: {pending[0].get('roll_number')}")

        if not pending:
            print("❌ No submissions found to test.")
            return

        target = pending[0]
        roll_number = target.get("roll_number")
        print(f"🚀 Triggering evaluation for Roll No: {roll_number}")

        eval_resp = requests.post(f"{BASE_URL}/api/ai-evaluate/{roll_number}")
        
        if eval_resp.status_code == 200:
            print("✅ Evaluation Successful!")
            print(json.dumps(eval_resp.json(), indent=2))
        else:
            print(f"❌ Evaluation Failed: {eval_resp.status_code}")
            print(eval_resp.text)

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

if __name__ == "__main__":
    test_integration()
