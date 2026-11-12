import sys
import pandas as pd

# Initialize app just in case

from app.services.ftel_dvr_service import FtelDvrScanner
df = pd.DataFrame([{"Mã shop": "Test", "IP": "8.8.8.8"}])
worker = FtelDvrScanner(df)

def on_log(m, c): print("LOG:", m)
def on_progress(c, t): print(f"PROG: {c}/{t}")
def on_checked(i, st, cs, cd, lat, pwd): print("ROW:", i, st)
def on_finished(res): print("FINISHED:", len(res))

worker.on_log = on_log
worker.on_progress = on_progress
worker.on_row_checked = on_checked
worker.on_finished = on_finished

worker.run()
