from pathlib import Path
import sys
import json
import pandas as pd

from app.services import backend_check
def mock_process_single_ip(row, col_map):
    return [{
        "MaShop": row[col_map["code"]],
        "TenShop": row[col_map["name"]],
        "IP_DauGhi": row[col_map["ip"]],
        "Brand": "HIK",
        "Port": 81,
        "ChiTiet": "Camera 1",
        "IP_Cam_Con": "",
        "Port_Cam_Con": "",
        "TrangThai": "Mất Playback",
        "LastRecordTime": "2024-01-01 10:00:00",
        "GhiChu": "",
        "PhanLoai": "NORMAL"
    }]
backend_check.process_single_ip = mock_process_single_ip

from app.api.routes.camera_router import check_camera_task, JOB_STORE
import shutil


def test_react():
    shutil.copy("test_cam.csv", "test_cam_react.csv")
    job_id = "test-job-2"
    JOB_STORE[job_id] = {
        "status": "queued",
        "progress": 0,
        "total": 0,
        "results": [],
        "error": None,
        "mode": "camera",
        "metrics": {},
        "results_dict": {},
        "cycle": 0
    }
    check_camera_task(job_id, "test_cam_react.csv", {"vaccine": True, "lc": True})
    return JOB_STORE[job_id]

if __name__ == "__main__":
    r = test_react()
    r_res = len(r.get("results", []))
    
    print(f"React Count: {r_res}")
    
    with open("golden_react2.json", "w", encoding="utf-8") as f:
        json.dump(r.get("results", []), f, ensure_ascii=False, indent=2)
        
    try:
        with open(Path(__file__).resolve().parents[1] / "fixtures" / "golden_legacy2.json", "r", encoding="utf-8") as f:
            legacy_data = json.load(f)
        l_res = len(legacy_data)
        print(f"Legacy Count: {l_res}")
        if r_res == l_res:
            print("Golden test parity OK.")
        else:
            print("Golden test mismatch!")
    except FileNotFoundError:
        print("No golden_legacy2.json fixture found to compare against.")
        
    print("Golden test complete.")
