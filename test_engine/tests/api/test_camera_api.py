from pathlib import Path
import requests
import time
import sys

URL = "http://127.0.0.1:18020/api/camera/jobs"

print("--- Testing Camera ---")
files = {'file': ('sample_dvr.csv', open(Path(__file__).resolve().parents[1] / "fixtures" / "sample_dvr.csv", 'rb'), 'text/csv')}
data = {'vaccine': False, 'lc': False}

res = requests.post(URL, files=files, data=data)
if res.status_code != 200:
    print("Failed", res.text)
    sys.exit(1)
    
job_id = res.json()['data']['job_id']
print(f"Job started: {job_id}")

for _ in range(30):
    state = requests.get(f"http://127.0.0.1:18020/api/camera/jobs/{job_id}").json()['data']
    print(f"Status: {state['status']}, Progress: {state['progress']}/{state.get('total', 0)}")
    if state['status'] in ['completed', 'failed', 'cancelled']:
        if state['status'] == 'failed':
            print("Error:", state.get('error'))
        break
    time.sleep(2)
print("Done.")
