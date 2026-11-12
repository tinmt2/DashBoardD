from pathlib import Path
import pandas as pd
from app.services import check_cam_service, backend_check
df_in = check_cam_service.read_input_file('test_cam.csv')
df_process = check_cam_service.filter_shops(df_in, {'vaccine': True, 'lc': True})
col_map = check_cam_service.detect_columns(df_process)
for _, row in df_process.iterrows():
    print(backend_check.process_single_ip(row, col_map))
