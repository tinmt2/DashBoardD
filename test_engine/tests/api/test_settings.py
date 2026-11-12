from pathlib import Path
import requests

def test_settings():
    print("Testing GET /api/settings...")
    res = requests.get("http://127.0.0.1:18020/api/settings")
    data = res.json()
    print("GET OK", data["data"]["paths"])

    print("Testing PUT /api/settings...")
    res = requests.put("http://127.0.0.1:18020/api/settings", json={"paths": {"warehouse_file": "D:/dummy/warehouse.xlsx"}})
    print("PUT OK", res.json())
    
    print("Testing GET /api/settings again to verify persistence...")
    res = requests.get("http://127.0.0.1:18020/api/settings")
    data = res.json()
    print("GET AFTER PUT OK", data["data"]["paths"])

    print("Testing Check Camera fallback...")
    res = requests.post("http://127.0.0.1:18020/api/camera/jobs", data={"mode": "camera", "vaccine": False, "lc": False})
    print("Check Camera Fallback OK", res.json())

if __name__ == "__main__":
    test_settings()
