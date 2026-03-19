"""Test the API endpoints."""
import requests
import json

print("=" * 50)
print("Testing EduSum API Endpoints")
print("=" * 50)

# Test dashboard endpoint
print('\nTesting Dashboard...')
try:
    r = requests.get('http://localhost:8000/api/v1/users/user_001')
    if r.status_code == 200:
        data = r.json()
        print('[OK] Dashboard endpoint works')
        print('  User: ' + data.get("user", {}).get("name", "N/A"))
        print('  Uploads: ' + str(data.get("uploads_count", 0)))
        print('  Avg Score: {:.1f}%'.format(data.get("performance", {}).get("avg_score", 0)))
    else:
        print('[ERROR] Status: ' + str(r.status_code))
except Exception as e:
    print('[ERROR] ' + str(e))

# Test leaderboard endpoint
print('\nTesting Leaderboard...')
try:
    r = requests.get('http://localhost:8000/api/v1/leaderboard')
    if r.status_code == 200:
        data = r.json()
        print('[OK] Leaderboard endpoint works')
        print('  Total users: ' + str(len(data)))
        if len(data) > 0:
            print('  Top user: ' + data[0].get("name") + ' (Score: {:.1f})'.format(data[0].get("score", 0)))
            print('  Uploads: ' + str(data[0].get("uploads_count", 0)))
    else:
        print('[ERROR] Status: ' + str(r.status_code))
except Exception as e:
    print('[ERROR] ' + str(e))

print("\n" + "=" * 50)
