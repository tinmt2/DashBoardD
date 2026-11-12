from pathlib import Path
import requests
import time
import sys

URL = "http://127.0.0.1:18020/api/ticket/jobs"

# 1. Start Job A
print("Starting Job A...")
files = {'file': ('sample_ticket.csv', open(Path(__file__).resolve().parents[1] / "fixtures" / "sample_ticket.csv", 'rb'), 'text/csv')}
data = {'ticket_type': 'Camera MKN'}

res_a = requests.post(URL, files=files, data=data)
if res_a.status_code != 200:
    print("Failed to start Job A", res_a.text)
    sys.exit(1)
    
job_a_id = res_a.json()['data']['job_id']
print(f"Job A started: {job_a_id}")

# 2. Start Job B (Should fail due to lock)
print("Starting Job B while Job A is running...")
files_b = {'file': ('sample_ticket.csv', open(Path(__file__).resolve().parents[1] / "fixtures" / "sample_ticket.csv", 'rb'), 'text/csv')}
res_b = requests.post(URL, files=files_b, data=data)
print(f"Job B Response: {res_b.status_code} - {res_b.text}")
if res_b.status_code == 409:
    print("OK: Single-job lock works!")
else:
    print("FAIL: Single-job lock failed!")

# 3. Poll Job A
print("Polling Job A...")
for _ in range(60):
    res = requests.get(f"{URL}/{job_a_id}")
    state = res.json()['data']
    if state['logs']:
        last_log = state['logs'][-1]['msg']
        print(f"Status: {state['status']}, Progress: {state['progress']}/{state['total']} | Log: {last_log}")
    else:
        print(f"Status: {state['status']}, Progress: {state['progress']}/{state['total']} | Log: none")

    if state['status'] in ['completed', 'failed', 'cancelled']:
        print("Final Results:")
        for r in state['results']:
            print("  ", r.get('ma_shop'), "->", r.get('ticket_id'))
        break
    time.sleep(2)

print("\nTesting Cancel...")
# Start Job C and cancel it
files_c = {'file': ('sample_ticket.csv', open(Path(__file__).resolve().parents[1] / "fixtures" / "sample_ticket.csv", 'rb'), 'text/csv')}
res_c = requests.post(URL, files=files_c, data=data)
job_c_id = res_c.json()['data']['job_id']
print(f"Job C started: {job_c_id}")
time.sleep(1)
res_cancel = requests.post(f"{URL}/{job_c_id}/cancel")
print("Cancel response:", res_cancel.json())
time.sleep(2)
state_c = requests.get(f"{URL}/{job_c_id}").json()['data']
print(f"Job C status after cancel: {state_c['status']}")

print("Done testing.")
