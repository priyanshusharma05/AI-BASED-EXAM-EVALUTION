import requests
import json

BASE_URL = "https://exam-system-backend.onrender.com"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {method} {url}...")
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"Status: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
            
        if response.status_code == expected_status:
            print("✅ PASS")
            return True
        else:
            print(f"❌ FAIL (Expected {expected_status})")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    print("-" * 50)

print("🚀 Starting Deployment Verification...")
print("-" * 50)

# 1. Test Root
test_endpoint("GET", "/")

# 2. Test Health
test_endpoint("GET", "/health")

# 3. Test Dashboard Stats
test_endpoint("GET", "/api/dashboard-stats")

# 4. Test Login (Expect 401 with invalid creds - confirms endpoint works)
test_endpoint("POST", "/api/login", {
    "email": "test@example.com",
    "password": "wrongpassword",
    "role": "student"
}, expected_status=401)
