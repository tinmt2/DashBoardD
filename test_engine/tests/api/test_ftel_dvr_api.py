from pathlib import Path
import requests
import time
import sys

URL = "http://127.0.0.1:18020/api/ftel-dvr/jobs"

print("--- Testing Ftel DVR ---")
files = {'file': ('sample_dvr.csv', open(Path(__file__).resolve().parents[1] / "fixtures" / "sample_dvr.csv", 'rb'), 'text/csv')}

res = requests.post(URL, files=files)
if res.status_code != 200:
    print("Failed", res.text)
    sys.exit(1)
    
job_id = res.json()['data']['job_id']
print(f"Job started: {job_id}")

for _ in range(30):
    state = requests.get(f"http://127.0.0.1:18020/api/ftel-dvr/jobs/{job_id}").json()['data']
    last_log = state['logs'][-1]['msg'] if state['logs'] else "none"
    print(f"Status: {state['status']}, Progress: {state['progress']}/{state['total']} | Log: {last_log}")
    if state['status'] in ['completed', 'failed', 'cancelled']:
        break
    time.sleep(2)
print("Done.")
