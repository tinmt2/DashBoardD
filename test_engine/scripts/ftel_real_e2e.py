import requests
import time
import sys
from datetime import datetime
import json
import os

BASE_URL = "http://127.0.0.1:18020/api/ftel-dvr"
REPORT_FILE = "FTEL_REAL_E2E_RESULT.md"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = f"[{ts}] {msg}"
    print(out)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(out + "\n")

def check_env():
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)
    log("# FTEL DVR REAL E2E TEST RESULT")
    log("## Execution Log")

def test_01_data_load():
    log("--- TEST 01: Data Load ---")
    try:
        res = requests.get(f"{BASE_URL}/data?refresh=false", timeout=10)
        log(f"GET /data?refresh=false -> Status: {res.status_code}")
        data = res.json()
        log(f"Response keys: {list(data.keys())}")
        if data.get("success"):
            records = data.get("data", [])
            log(f"Loaded {len(records)} records.")
            if len(records) > 0:
                log(f"Sample record keys: {list(records[0].keys())}")
        return True
    except Exception as e:
        log(f"Exception: {e}")
        return False

def test_02_03_scan_start_and_polling():
    log("--- TEST 02 & 03: Scan Start & Polling ---")
    try:
        res = requests.post(f"{BASE_URL}/scan/start", timeout=10)
        log(f"POST /scan/start -> Status: {res.status_code}")
        log(f"Response: {res.text}")
        
        for i in range(5):
            res_status = requests.get(f"{BASE_URL}/status", timeout=5)
            st = res_status.json()
            log(f"Polling {i+1} -> state: {st.get('state')}, progress: {st.get('progress')}/{st.get('total')}")
            time.sleep(2)
        return True
    except Exception as e:
        log(f"Exception: {e}")
        return False

def test_04_05_cancel_and_restart():
    log("--- TEST 04 & 05: Cancel & Restart ---")
    try:
        res = requests.post(f"{BASE_URL}/scan/stop", timeout=10)
        log(f"POST /scan/stop -> Status: {res.status_code}")
        
        time.sleep(2)
        res_status = requests.get(f"{BASE_URL}/status", timeout=5)
        log(f"State after cancel: {res_status.json().get('state')}")
        
        res_restart = requests.post(f"{BASE_URL}/scan/start", timeout=10)
        log(f"POST /scan/start (Restart) -> Status: {res_restart.status_code}")
        return True
    except Exception as e:
        log(f"Exception: {e}")
        return False

def test_06_concurrent_start():
    log("--- TEST 06: Concurrent Start ---")
    try:
        res = requests.post(f"{BASE_URL}/scan/start", timeout=10)
        log(f"POST /scan/start (Concurrent) -> Status: {res.status_code}")
        log(f"Response: {res.text}")
        return True
    except Exception as e:
        log(f"Exception: {e}")
        return False

def test_07_auto_login(ip, port, password):
    log("--- TEST 07: Auto Login ---")
    if not ip or not password:
        log("Skipped Auto Login - No credentials provided.")
        return False
    try:
        payload = {"ip": ip, "port": port, "password": password}
        log(f"POST /auto-login -> ip: {ip}, port: {port}, password: ***")
        res = requests.post(f"{BASE_URL}/auto-login", json=payload, timeout=60)
        log(f"Status: {res.status_code}")
        log(f"Response: {res.text}")
        return True
    except Exception as e:
        log(f"Exception: {e}")
        return False

if __name__ == "__main__":
    check_env()
    log("Starting FTEL DVR E2E API Tests...")
    test_01_data_load()
    test_02_03_scan_start_and_polling()
    test_06_concurrent_start()
    test_04_05_cancel_and_restart()
    
    # Cancel again to clean up
    requests.post(f"{BASE_URL}/scan/stop")
    
    print("\n--- Auto Login Test ---")
    test_ip = input("Enter test DVR IP (or press Enter to skip): ").strip()
    if test_ip:
        test_port = int(input("Enter port (default 81): ").strip() or "81")
        test_password = input("Enter password: ").strip()
        test_07_auto_login(test_ip, test_port, test_password)
    
    log("Finished FTEL DVR E2E API Tests.")
    print(f"\nResult saved to {REPORT_FILE}. Please send this file back to the agent.")
