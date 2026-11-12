from pathlib import Path
import asyncio
import sys
import pandas as pd
from app.api.routes import ftel_dvr_router

def golden_test():
    print("MOCKING GSHEET DATA...")
    # Mock gsheet_sync to return a small dataframe
    from app.services import gsheet_sync
    def mock_read_ticket_sheet(name):
        return True, pd.DataFrame([
            {"Mã shop": "Test_Local", "Tên shop": "Shop Local", "Vùng": "HCM", "IP": "127.0.0.1", "Mật khẩu": "mock_pass1"},
            {"Mã shop": "Test_Google", "Tên shop": "Google DNS", "Vùng": "HN", "IP": "8.8.8.8", "Mật khẩu": "mock_pass2"},
            {"Mã shop": "Test_Unreachable", "Tên shop": "Fake IP", "Vùng": "DN", "IP": "10.255.255.255", "Mật khẩu": "mock_pass3"}
        ])
    gsheet_sync.read_ticket_sheet = mock_read_ticket_sheet

    print("TESTING /data...")
    res = asyncio.run(ftel_dvr_router.get_ftel_data(refresh=True))
    if res.success:
        print("Data loaded:", len(res.data), "rows")
    else:
        print("Error:", res.message)

    print("TESTING /scan/start...")
    res2 = asyncio.run(ftel_dvr_router.start_ftel_scan())
    print("Scan started:", res2.success)

    print("WAITING FOR SCAN...")
    import time
    while ftel_dvr_router.FTEL_STATE["status"] == "running":
        time.sleep(1)
        print(f"Progress: {ftel_dvr_router.FTEL_STATE['progress']} / {ftel_dvr_router.FTEL_STATE['total']}")

    print("SCAN FINISHED:", ftel_dvr_router.FTEL_STATE["status"])
    for r in ftel_dvr_router.FTEL_STATE["results"]:
        print(f"{r['ma_shop']} - {r['ip']}: {r['status']} | Latency: {r['latency']}")

golden_test()
