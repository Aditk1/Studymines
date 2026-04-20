
import requests

BASE_URL = "http://localhost:8000/api/v1"

def check_endpoint(name, method, path, data=None, files=None, headers=None, expected_status=200):
    url = f"{BASE_URL}{path}"
    print(f"Testing {name} [{method}] on {url}...")
    try:
        if method == "POST":
            resp = requests.post(url, data=data, files=files, headers=headers)
        elif method == "GET":
            resp = requests.get(url, params=data, headers=headers)
        
        status = resp.status_code
        if status == expected_status:
            print(f"  ✅ Status: {status} (Expected)")
        else:
            print(f"  ❌ Status: {status} (Expected {expected_status})")
            print(f"     Body: {resp.text[:200]}")
        return resp
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return None

def main():
    print("--- [EDU-RAG-PROD-TEST] Production-Level API Stress & Validation ---")
    
    # 1. Auth Failures
    check_endpoint("Login (Invalid)", "POST", "/auth/login", 
                   data={"email": "wrong@edu.com", "password": "wrong"}, 
                   expected_status=401)
    
    # 2. Duplicate Signup (Stress)
    # We'll use a random email to avoid collision but test if it fails on second try
    import uuid
    email = f"test_{uuid.uuid4().hex[:6]}@edu.com"
    check_endpoint("Signup (New)", "POST", "/auth/signup", 
                   data={"name": "QA Tester", "email": email, "password": "password123", "student_level": "undergraduate"})
    check_endpoint("Signup (Duplicate)", "POST", "/auth/signup", 
                   data={"name": "QA Tester", "email": email, "password": "password123", "student_level": "undergraduate"}, 
                   expected_status=400)

    # 3. Graph Query Validation (Missing Token)
    check_endpoint("Graph Query (No Token)", "POST", "/graph/query", 
                   data={"query": "test"}, expected_status=401)

    # 4. Large Upload (Boundary Test)
    # Creating a dummy file of 1MB (well below 50MB but checking logic)
    dummy_data = b"X" * 1024 * 1024
    check_endpoint("Document Upload (Missing Auth)", "POST", "/upload/document", 
                   files={"file": ("large.pdf", dummy_data, "application/pdf")},
                   expected_status=401)

    # 5. Public Content Test
    check_endpoint("Dashboard (Public Redirect/Fail)", "GET", "/leaderboard", expected_status=200)

    print("\n--- Testing Complete ---")

if __name__ == "__main__":
    main()
