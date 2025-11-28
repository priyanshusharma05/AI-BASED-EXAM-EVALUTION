import requests
import json

BASE_URL = "https://exam-system-backend.onrender.com"
# BASE_URL = "http://127.0.0.1:5000" # Uncomment to test locally

def test_get_student_submissions(email):
    print(f"Testing for student: {email}")
    try:
        url = f"{BASE_URL}/api/get-student-submissions?student={email}"
        print(f"Requesting: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            submissions = data.get("submissions", [])
            print(f"✅ Success! Found {len(submissions)} submissions.")
            for sub in submissions:
                print(f" - {sub.get('exam_name')} ({sub.get('subject')}): {sub.get('status')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Test with the email seen in the screenshot
    test_get_student_submissions("kunalsinghal121@gmail.com")
    # Test with different casing
    test_get_student_submissions("Kunalsinghal121@gmail.com")
