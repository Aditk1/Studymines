import requests
import json

print("=== Running Integration Test for master_eduRAG ===")

# 1. Test Health Endpoint
print("\n1. Testing Health Endpoint (GET /)")
try:
    health_resp = requests.get("http://localhost:8000/")
    print(f"Status = {health_resp.status_code}")
    print(json.dumps(health_resp.json(), indent=2))
except Exception as e:
    print(f"Failed to reach health endpoint: {e}")

# 2. Test Document Upload Endpoint
print("\n2. Testing /api/v1/upload/document with a dummy text file...")
dummy_text = """
Photosynthesis is a system of biological processes by which photosynthetic organisms, such as most plants, algae, and cyanobacteria, convert light energy, typically from sunlight, into the chemical energy necessary to fuel their cellular activities.
"""
with open("test_dummy.txt", "w", encoding="utf-8") as f:
    f.write(dummy_text)

files = {'file': ('test_dummy.txt', open('test_dummy.txt', 'rb'), 'text/plain')}
data = {
    'user_id': 'test_guest',
    'student_level': 'undergraduate',
    'subject': 'Biology',
    'topic': 'Photosynthesis'
}

try:
    upload_resp = requests.post("http://localhost:8000/api/v1/upload/document", files=files, data=data)
    print(f"Status = {upload_resp.status_code}")
    try:
        res = upload_resp.json()
        print("Success! Received Study Package:")
        if "study_package" in res and "data" in res["study_package"]:
            data_keys = list(res["study_package"]["data"].keys())
            print(f"  -> Generated features: {data_keys}")
        else:
            print("  -> Response:", json.dumps(res, indent=2))
    except Exception:
        print(f"  -> Error Response: {upload_resp.text}")
except Exception as e:
    print(f"Failed to upload document: {e}")

print("\n=== Test Complete ===")
