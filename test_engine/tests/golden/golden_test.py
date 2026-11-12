from pathlib import Path
import asyncio
import os
import sys

from app.api.routes import camera_router
from app.services import backend_check

import time

def run():
    job_id = "test_job"
    camera_router.JOB_STORE[job_id] = {
        "status": "queued",
        "progress": 0,
        "total": 0,
        "results": [],
        "error": None
    }
    
    file_path = "sample.csv"
    filter_opts = {"vaccine": False, "lc": False}
    
    print("Starting job...")
    camera_router.check_camera_task(job_id, file_path, filter_opts)
    
    state = camera_router.JOB_STORE[job_id]
    print(f"Status: {state['status']}")
    print(f"Error: {state['error']}")
    print(f"Results: {len(state['results'])}")
    for r in state['results']:
        print(f"  {r['MaShop']} - {r['TrangThai']} - {r['IP_DauGhi']}")

if __name__ == "__main__":
    run()
