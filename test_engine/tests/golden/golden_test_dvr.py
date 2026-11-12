from pathlib import Path
import asyncio
import os
import sys

from app.api.routes import ftel_dvr_router
import time

def run():
    job_id = "test_dvr_job"
    
    file_path = "sample_dvr.csv"
    
    # Run the equivalent of the FastAPI logic
    import pandas as pd
    from app.services.ftel_dvr_service import FtelDvrScanner
    
    df_in = pd.read_csv(file_path)
    worker = FtelDvrScanner(df_in)
    
    ftel_dvr_router.JOB_STORE[job_id] = {
        "status": "running",
        "progress": 0,
        "total": len(df_in),
        "results": [],
        "logs": [],
        "error": None,
        "_worker": worker 
    }
    
    def on_log(msg, color):
        print(f"[{color}] {msg}")
        
    def on_progress(completed, total):
        print(f"Progress: {completed}/{total}")
            
    def on_finished(results):
        ftel_dvr_router.JOB_STORE[job_id]["status"] = "completed"
        ftel_dvr_router.JOB_STORE[job_id]["results"] = results
            
    worker.log_signal.connect(on_log)
    worker.progress_signal.connect(on_progress)
    worker.finished_signal.connect(on_finished)
    
    worker.start()
    worker.wait()
    
    state = ftel_dvr_router.JOB_STORE[job_id]
    print(f"Status: {state['status']}")
    print(f"Results: {len(state['results'])}")
    for r in state['results']:
        print(f"  {r['ma_shop']} - {r['status']} - {r['ip']} - {r['cam_status']}")

if __name__ == "__main__":
    run()
