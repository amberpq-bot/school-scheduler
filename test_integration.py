import urllib.request
import json
import time
import sys

def test_solve():
    url = "http://localhost:8000/api/solve"
    
    # Sample Data
    payload = {
        "teachers": [
            {"id": "t1", "name": "Mr. Smith", "qualifications": ["Math"]},
            {"id": "t2", "name": "Ms. Jones", "qualifications": ["Science"]}
        ],
        "rooms": [
            {"id": "r1", "name": "Room 101", "capacity": 30}
        ],
        "classes": [
            {"id": "c1", "name": "Math 101", "subject": "Math", "required_sessions": 2},
            {"id": "c2", "name": "Science 101", "subject": "Science", "required_sessions": 2}
        ],
        "time_slots": [
            {"id": "s1", "day": "Mon", "period": 1},
            {"id": "s2", "day": "Mon", "period": 2},
            {"id": "s3", "day": "Mon", "period": 3},
            {"id": "s4", "day": "Mon", "period": 4},
            {"id": "s5", "day": "Mon", "period": 5}
        ]
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"FAILED: Status {response.status}")
                return False
            
            data = json.loads(response.read().decode('utf-8'))
            print("Response:", json.dumps(data, indent=2))
            
            if data['status'] == 'OPTIMAL':
                print("PASSED: Schedule generated successfully")
                return True
            else:
                print("FAILED: Status not OPTIMAL")
                return False
                
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    # Wait for server to start
    time.sleep(2)
    sys.exit(0 if test_solve() else 1)
