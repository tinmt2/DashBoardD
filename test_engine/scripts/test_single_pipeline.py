import asyncio
import sys
import pandas as pd
from app.api.routes import ftel_dvr_router
import time

def golden_test():
    print("MOCKING GSHEET DATA...")
    # Mock gsheet_sync to return a small dataframe with the real IP
    from app.services import gsheet_sync
    def mock_read_ticket_sheet(name):
        return True, pd.DataFrame([
            {"Mã shop": "Test_Real", "Tên shop": "Test Shop", "Vùng": "HN", "IP": "118.70.151.108", "Mật khẩu": "Dvkt#17011#@!"}
        ])
    gsheet_sync.read_ticket_sheet = mock_read_ticket_sheet

    print("TESTING /data...")
    res = asyncio.run(ftel_dvr_router.get_ftel_data(refresh=True))
    if res.success:
        print("Data loaded:", len(res.data), "rows")
    
    print("TESTING /scan/start...")
    asyncio.run(ftel_dvr_router.start_ftel_scan())

    while ftel_dvr_router.FTEL_STATE["status"] == "running":
        time.sleep(2)
        print(f"Progress: {ftel_dvr_router.FTEL_STATE['progress']} / {ftel_dvr_router.FTEL_STATE['total']}")
        for r in ftel_dvr_router.FTEL_STATE["results"]:
            if r['status'] != "Chưa check":
                print(f"Checked: {r['ma_shop']} - {r['ip']} | Status: {r['status']}")
                print(f"Cam Status: {r['cam_status']}")
                print(f"Cam Online: {r['cam_online']}")
                print(f"Cam Total: {r['cam_total']}")

    print("SCAN FINISHED:", ftel_dvr_router.FTEL_STATE["status"])
    for r in ftel_dvr_router.FTEL_STATE["results"]:
        print(r)

if __name__ == "__main__":
    golden_test()
