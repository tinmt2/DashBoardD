import os




import re




import time




import traceback




from collections.abc import Callable




from datetime import datetime




from pathlib import Path









import gspread




import pandas as pd




from oauth2client.service_account import ServiceAccountCredentials









from app.config import get_config  # type: ignore




from app.paths import BASE_DIR  # type: ignore














def retry_gsheet(retries: int = 3, delay: float = 2.0):




    def decorator(func: Callable):




        def wrapper(*args, **kwargs):




            last_exc = None




            for i in range(retries):




                try:




                    return func(*args, **kwargs)




                except Exception as e:




                    last_exc = e




                    if "quota" in str(e).lower():




                        time.sleep(delay * 5) # Longer sleep for quota




                    else:




                        time.sleep(delay * (i + 1))




            raise last_exc




        return wrapper




    return decorator
















def _format_error(e: Exception) -> str:
    msg = str(e).strip()
    if not msg and getattr(e, '__cause__', None):
        msg = str(e.__cause__).strip()
    if not msg and getattr(e, '__context__', None):
        msg = str(e.__context__).strip()
    if not msg:
        msg = repr(e)
    return msg


def _parse_spreadsheet_id(value: str) -> str:




    if not value:




        return ""




    value = value.strip()




    m = re.search(r"/d/([a-zA-Z0-9-_]+)", value)




    if m:




        return m.group(1)




    return value














_CFG = get_config().get("gsheet", {})




TARGET_SPREADSHEET_ID = _parse_spreadsheet_id(




    os.getenv("CHECKCAM_SPREADSHEET_ID", _CFG.get("spreadsheet_id", "1hK2NYEjELl-8qapOQ72nS3E2iKrOAz9BwsLACZDcEaQ"))




)




TARGET_GID = int(os.getenv("CHECKCAM_TARGET_GID", _CFG.get("target_gid", "1062029638")))




TARGET_GID_ONLINE = 640361867




TARGET_GID_PLAYBACK = 167867828




TARGET_GID_DVR = 1955757828




TARGET_GID_HDD = 327583410




DEFAULT_CRED_FILE = os.getenv(




    "CHECKCAM_CRED_FILE",




    str(BASE_DIR / _CFG.get("cred_file", "Checkcam.json")),




)









# Fix encoding: Use the values from config or safe defaults




SHEET_CAM_MKN = os.getenv("CHECKCAM_SHEET_CAM_MKN", _CFG.get("sheet_cam_mkn", "Cam mkn"))




SHEET_SUMMARY = os.getenv("CHECKCAM_SHEET_SUMMARY", _CFG.get("sheet_summary", "Tổng Camera"))




SHEET_NO_DATA = os.getenv("CHECKCAM_SHEET_NO_DATA", _CFG.get("sheet_no_data", "Cam không có playback"))




SHEET_HDD = os.getenv("CHECKCAM_SHEET_HDD", _CFG.get("sheet_hdd", "Lỗi ổ cứng"))




SHEET_DVR = os.getenv("CHECKCAM_SHEET_DVR", _CFG.get("sheet_dvr", "Lỗi đầu ghi"))




SHEET_ONLINE = os.getenv("CHECKCAM_SHEET_ONLINE", _CFG.get("sheet_online", "Cam phục hồi"))



















def _make_unique_headers(headers) -> list:




    seen = {}




    unique_headers = []




    for h in headers:




        h_str = str(h).strip()




        if not h_str:




            h_str = "Unnamed"




        h_lower = h_str.lower()




        if h_lower in seen:




            seen[h_lower] += 1




            unique_headers.append(f"{h_str}_{seen[h_lower]}")




        else:




            seen[h_lower] = 1




            unique_headers.append(h_str)




    return unique_headers














def _resolve_cred_file(cred_file: str | None = None) -> str:




    path = Path(cred_file or DEFAULT_CRED_FILE)




    if not path.is_absolute():




        path = BASE_DIR / path




    return str(path)














# Global Cache




_CACHED_CLIENT = None




_CACHED_SH = None









def get_client(cred_file: str | None = None, force_refresh: bool = False):




    global _CACHED_CLIENT




    if _CACHED_CLIENT and not force_refresh:




        return _CACHED_CLIENT









    scope = [




        "https://spreadsheets.google.com/feeds",




        "https://www.googleapis.com/auth/drive",




    ]




    cred_path = _resolve_cred_file(cred_file)




    if not os.path.exists(cred_path):




        raise FileNotFoundError(f"Credential file not found at: {cred_path}")




    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)




    _CACHED_CLIENT = gspread.authorize(creds)




    return _CACHED_CLIENT














def _get_worksheet(client, sheet_name: str):




    global _CACHED_SH




    if _CACHED_SH is None:




        _CACHED_SH = client.open_by_key(TARGET_SPREADSHEET_ID)




    




    # Optional: If client changed, we should probably re-open




    # but for this app's lifecycle, the client is usually the same.




    try:




        return _CACHED_SH.worksheet(sheet_name)




    except Exception:




        # If worksheet operation fails (maybe token expired?), try to re-open spreadsheet




        _CACHED_SH = client.open_by_key(TARGET_SPREADSHEET_ID)




        return _CACHED_SH.worksheet(sheet_name)














def _write_column(worksheet, col_letter: str, values) -> tuple[bool, str]:




    if not values:




        return False, "Khong co du lieu de ghi"




    start_row = 2




    end_row = start_row + len(values) - 1




    range_name = f"{col_letter}{start_row}:{col_letter}{end_row}"




    worksheet.update(range_name, [[str(v) if v is not None else ""] for v in values])




    return True, f"Da cap nhat {len(values)} dong vao cot {col_letter}"














@retry_gsheet(retries=3)




def sync_data(df_ticket, cred_file: str | None = None):




    """Original behavior: Full overwrite for Summary Sheet."""




    



    try:



        client = get_client(cred_file)



        sh = client.open_by_key(TARGET_SPREADSHEET_ID)



        



        worksheet = next((ws for ws in sh.worksheets() if ws.id == TARGET_GID), None)



        if worksheet is None:



            worksheet = sh.worksheet(SHEET_SUMMARY)







        if df_ticket.empty:



            worksheet.clear()



            return True, "Khong co du lieu, da clear sheet 1"













        # Cleanup: Prepare copy and numeric conversion for Mã shop




        df_copy = df_ticket.copy()




        for col in df_copy.columns:




            if "Mã shop" in col or "Ma shop" in col:




                df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0).astype(int)




            else:




                df_copy[col] = df_copy[col].astype(str)









        if worksheet is None:




            return False, f"Khong tim thay worksheet voi GID {TARGET_GID}"









        # Sorting




        day_col = next((c for c in df_copy.columns if str(c).strip().lower() == "số ngày offline"), None)




        if day_col:




            import re




            def sort_key(val):




                s = str(val).strip().lower()




                if "lâu ngày" in s or "lâu" in s: return 9999




                try: return int(re.sub(r'\D', '', s))




                except: return 0




            df_copy['__sort_val__'] = df_copy[day_col].apply(sort_key)




            df_copy = df_copy.sort_values(by='__sort_val__', ascending=False).drop(columns=['__sort_val__'])









        # Method: Full overwrite (as originally requested)




        payload = [df_copy.columns.values.tolist()] + df_copy.values.tolist()




        worksheet.clear()




        worksheet.update(payload)




        return True, "Dong bo thanh cong (Sheet 1 Overwrite)"




    except Exception as e:




        return False, f"Loi dong bo Sheet 1: {_format_error(e)}"




@retry_gsheet(retries=3)




def upsert_worksheet_data(worksheet, df_new, key_cols, status_col_index=8):




    """




    Update or Insert data into a worksheet.




    - Preserves existing columns (like Ticket IDs).




    - Updates common columns (Days, Status).




    - Checks by key_cols.




    - Sets status_col_index to 'mới phát sinh' for new rows and 'chưa xử lý' for updated rows.




    """




    try:




        data = worksheet.get_all_values()




        




        is_empty = True




        if data:




            for row in data:




                if any(str(cell).strip() for cell in row):




                    is_empty = False




                    break




                    




        if is_empty:




            # Empty sheet: Just upload with headers




            payload = [df_new.columns.values.tolist()] + df_new.values.tolist()




            worksheet.clear()




            worksheet.update(payload)




            return True, f"Da tao moi {len(df_new)} dong"









        # 1. PREPARE EXISTING DATA & HEADERS




        # Strip headers to be robust against "Mã shop " vs "Mã shop"




        raw_headers = _make_unique_headers(data[0])




        df_existing = pd.DataFrame(data[1:], columns=raw_headers)




        




        # Mapping: df_new columns -> existing sheet columns (insensitive match)


        # ALIAS MAPPING FOR CHECK CAMERA


        aliases = {


            "cam đã online": ["camera", "cam", "số cam"],


            "danh sách cam lỗi": ["camera", "cam", "số cam"],


            "số cam": ["camera", "cam", "danh sách cam lỗi"],


            "số ngày không có playback": ["ngày không playback", "số ngày offline", "ngày offline", "ngày không có playback"],


            "cam mới offline": ["camera", "cam", "số cam"],


        }


        


        header_map = {}


        for col_new in df_new.columns:


            cn = col_new.strip().lower()


            match = next((h for h in raw_headers if h.strip().lower() == cn), None)


            if not match and cn in aliases:


                for alias in aliases[cn]:


                    match = next((h for h in raw_headers if h.strip().lower() == alias), None)


                    if match:


                        break


            if match:


                header_map[col_new] = match












        # 2. NORMALIZE KEYS




        def normalize_key(val):




            # Extremely aggressive normalization




            return str(val or "").strip().lower().replace(".0", "").replace(" ", "")









        # key -> row_index in df_existing




        existing_keys = {}




        for idx, row in df_existing.iterrows():




            k = tuple(normalize_key(row.get(header_map.get(c, c), "")) for c in key_cols)




            existing_keys[k] = idx









        # 3. ENSURE STATUS COLUMN




        target_idx = status_col_index - 1




        while len(df_existing.columns) <= target_idx:




            new_col_name = "Trạng thái xử lý" if len(df_existing.columns) == target_idx else f"Col_{len(df_existing.columns)}"




            df_existing[new_col_name] = ""




        




        status_col_actual_name = df_existing.columns[target_idx]









        # 4. PERFORM UPSERT




        new_rows = []




        updated_indices = set()




        for _, row_new in df_new.iterrows():




            k = tuple(normalize_key(row_new.get(c, "")) for c in key_cols)




            




            if k in existing_keys:




                idx = existing_keys[k]




                updated_indices.add(idx)




                # Update matched columns




                for col_new, col_actual in header_map.items():




                    df_existing.at[idx, col_actual] = str(row_new[col_new])




                # Mark status (Recurring)




                df_existing.at[idx, status_col_actual_name] = "chưa xử lý"




            else:




                # Add new row




                new_row_dict = {c: "" for c in df_existing.columns}




                for col_new, col_actual in header_map.items():




                    if col_actual in new_row_dict:




                        new_row_dict[col_actual] = str(row_new[col_new])




                # Mark status (New)




                new_row_dict[status_col_actual_name] = "mới phát sinh"




                new_rows.append(new_row_dict)









        # 5. MARK RESOLVED




        for idx in df_existing.index:




            if idx not in updated_indices:




                # If it's already marked as 'đã xử lý', keep it. If it was 'chưa xử lý' or 'mới phát sinh' and now gone, mark 'đã xử lý'.




                curr_status = str(df_existing.at[idx, status_col_actual_name]).strip().lower()




                if curr_status != "đã xử lý":




                    df_existing.at[idx, status_col_actual_name] = "đã xử lý"









        if new_rows:




            df_existing = pd.concat([df_existing, pd.DataFrame(new_rows)], ignore_index=True)









        # --- SORTING Logic: Priority for longest offline days ---




        day_col = next((c for c in df_existing.columns if str(c).strip().lower() == "số ngày offline"), None)




        if day_col:




            import re




            def sort_key(val):




                s = str(val).strip().lower()




                if "lâu ngày" in s or "lâu" in s: return 9999




                try: return int(re.sub(r'\D', '', s))




                except: return 0




            




            df_existing['__sort_val__'] = df_existing[day_col].apply(sort_key)




            # Sort: MKN lâu ngày (9999) first, then numeric days descending




            df_existing = df_existing.sort_values(by='__sort_val__', ascending=False).drop(columns=['__sort_val__'])









        # 6. BATCH UPDATE




        out_headers = ["" if str(h).startswith("Unnamed") else h for h in df_existing.columns.values.tolist()]




        payload = [out_headers] + df_existing.values.tolist()




        worksheet.clear()




        worksheet.update(payload)




        return True, f"Da cap nhat {len(df_new)} dong (Row index 80228 check done)"




    except Exception as e:




        print(f"Upsert error: {e}")




        traceback.print_exc()




        return False, str(e)














def _match_online_header(col_name: str, sheet_headers: list) -> int | None:
    aliases = {
        "cam đã online": ["camera", "cam", "số cam"],
        "ngày online": ["ngày onine", "ngày online", "ngay online", "ngay onine"],
        "mã shop": ["ma shop"],
        "ma shop": ["mã shop"]
    }
    col_clean = str(col_name).strip().lower()
    for idx, h in enumerate(sheet_headers):
        hc = str(h).strip().lower()
        if hc == col_clean:
            return idx
        if col_clean in aliases and hc in aliases[col_clean]:
            return idx
    return None














@retry_gsheet(retries=3)




def sync_back_online(df_online, cred_file: str | None = None):
    try:
        import gspread
        import pandas as pd
        from app.services.gsheet_sync import get_client, TARGET_SPREADSHEET_ID, TARGET_GID_ONLINE, SHEET_ONLINE, _match_online_header
        
        if df_online is None or (isinstance(df_online, pd.DataFrame) and df_online.empty):
            df_online = pd.DataFrame()
        
        required_cols = ["Mã shop", "Tên shop", "Vùng", "Cam đã online", "Ticket", "Ngày online"]
        available_cols = [c for c in required_cols if c in df_online.columns]
        df_online = df_online[available_cols].copy()

        client = get_client(cred_file)
        sh = client.open_by_key(TARGET_SPREADSHEET_ID)
        worksheet = next((ws for ws in sh.worksheets() if ws.id == TARGET_GID_ONLINE), None)
        if worksheet is None:
            worksheet = sh.worksheet(SHEET_ONLINE)
        if worksheet is None:
            return False, f"Khong tim thay worksheet voi GID {TARGET_GID_ONLINE}"

        existing_data = worksheet.get_all_values()
        if not existing_data:
            payload = [df_online.columns.values.tolist()] + df_online.values.tolist()
            worksheet.update("A1", payload)
            return True, f"Da khoi tao va ghi {len(df_online)} cam online tu hang 2"

        raw_headers = [str(h).strip() for h in existing_data[0]]
        
        col_map = {}
        for c in df_online.columns:
            m_idx = _match_online_header(c, raw_headers)
            if m_idx is not None:
                col_map[c] = m_idx
        
        actual_data_rows = []
        for r in existing_data[1:]:
            if any(str(cell).strip() for cell in r):
                actual_data_rows.append(r)

        df_existing = pd.DataFrame(actual_data_rows, columns=raw_headers) if actual_data_rows else pd.DataFrame(columns=raw_headers)
        
        def normalize_key(val):
            return str(val or "").strip().lower().replace(".0", "").replace(" ", "")

        cam_col_idx = _match_online_header("Cam đã online", raw_headers)
        shop_col_idx = _match_online_header("Mã shop", raw_headers)

        existing_keys = set()
        key_to_sheet_row = {}
        
        for i, r in enumerate(existing_data):
            if i == 0: continue
            if not any(str(cell).strip() for cell in r): continue
            m_shop = r[shop_col_idx] if (shop_col_idx is not None and len(r) > shop_col_idx) else (r[0] if len(r) > 0 else "")
            c_online = r[cam_col_idx] if (cam_col_idx is not None and len(r) > cam_col_idx) else (r[3] if len(r) > 3 else "")
            k = (normalize_key(m_shop), normalize_key(c_online))
            existing_keys.add(k)
            key_to_sheet_row[k] = i + 1

        new_rows = []
        updates = []
        date_col_idx = _match_online_header("Ngày online", raw_headers)

        for _, row in df_online.iterrows():
            k = (normalize_key(row.get("Mã shop", "")), normalize_key(row.get("Cam đã online", "")))
            if k not in existing_keys:
                prepared_row = [""] * len(raw_headers)
                found_mapping = False
                for c, val in row.items():
                    if c in col_map:
                        prepared_row[col_map[c]] = str(val) if val is not None else ""
                        found_mapping = True
                if not found_mapping:
                    prepared_row = [str(x) if x is not None else "" for x in row.values.tolist()]
                new_rows.append(prepared_row)
            else:
                sheet_r_idx = key_to_sheet_row.get(k)
                if sheet_r_idx and date_col_idx is not None:
                    existing_row_data = existing_data[sheet_r_idx - 1]
                    existing_date = existing_row_data[date_col_idx] if len(existing_row_data) > date_col_idx else ""
                    new_date = str(row.get("Ngày online", ""))
                    
                    if not str(existing_date).strip() and str(new_date).strip():
                        updates.append({
                            "range": gspread.utils.rowcol_to_a1(sheet_r_idx, date_col_idx + 1),
                            "values": [[new_date]]
                        })

        msg_parts = []
        if new_rows:
            start_row = len(actual_data_rows) + 2
            end_row = start_row + len(new_rows) - 1
            range_name = f"A{start_row}"
            worksheet.update(range_name, new_rows, value_input_option="USER_ENTERED")
            msg_parts.append(f"Da ghi {len(new_rows)} cam online tu hang {start_row} den {end_row}")
        
        if updates:
            worksheet.batch_update(updates)
            msg_parts.append(f"Da cap nhat {len(updates)} ngay online")
            
        if not new_rows and not updates:
            return True, "Khong co cam online moi nao de ghi them"
            
        return True, ", ".join(msg_parts)
    except Exception as e:
        return False, f"Loi dong bo cam online: {_format_error(e)}"



@retry_gsheet(retries=3)




def sync_playback_errors(df_playback, cred_file: str | None = None):




    """Sync 'Cam không có playback' to GID 167867828 with Upsert."""




    try:




        if df_playback is None or (isinstance(df_playback, pd.DataFrame) and df_playback.empty):

            df_playback = pd.DataFrame()









        if isinstance(df_playback, list): df_playback = pd.DataFrame(df_playback)









        client = get_client(cred_file)




        sh = client.open_by_key(TARGET_SPREADSHEET_ID)




        worksheet = next((ws for ws in sh.worksheets() if ws.id == TARGET_GID_PLAYBACK), None)




        if not worksheet: return False, f"Khong tim thay worksheet GID {TARGET_GID_PLAYBACK}"









        # Keys for Playback




        keys = ["Mã shop", "Số cam"]




        return upsert_worksheet_data(worksheet, df_playback, keys, status_col_index=8)




    except Exception as e:




        return False, f"Loi dong bo cam playback: {_format_error(e)}"














@retry_gsheet(retries=3)




def sync_dvr_errors(df_dvr, cred_file: str | None = None):




    """Sync 'Lỗi đầu ghi' data to GID 1955757828 with Upsert."""




    try:




        if df_dvr is None or (isinstance(df_dvr, pd.DataFrame) and df_dvr.empty):

            df_dvr = pd.DataFrame()









        if isinstance(df_dvr, list): df_dvr = pd.DataFrame(df_dvr)









        client = get_client(cred_file)




        sh = client.open_by_key(TARGET_SPREADSHEET_ID)




        worksheet = next((ws for ws in sh.worksheets() if ws.id == TARGET_GID_DVR), None)




        if not worksheet: return False, f"Khong tim thay worksheet GID {TARGET_GID_DVR}"









        # Key for DVR




        keys = ["Mã shop"]




        return upsert_worksheet_data(worksheet, df_dvr, keys, status_col_index=8)




    except Exception as e:




        return False, f"Loi dong bo dau ghi: {_format_error(e)}"














@retry_gsheet(retries=3)




def sync_hdd_errors(df_hdd, cred_file: str | None = None):




    """Sync 'Lỗi ổ cứng' data to GID 327583410 with Upsert."""




    try:




        if df_hdd is None or (isinstance(df_hdd, pd.DataFrame) and df_hdd.empty):

            df_hdd = pd.DataFrame()









        if isinstance(df_hdd, list): df_hdd = pd.DataFrame(df_hdd)









        client = get_client(cred_file)




        sh = client.open_by_key(TARGET_SPREADSHEET_ID)




        worksheet = next((ws for ws in sh.worksheets() if ws.id == TARGET_GID_HDD), None)




        if not worksheet: return False, f"Khong tim thay worksheet GID {TARGET_GID_HDD}"









        # Key for HDD




        keys = ["Mã shop"]




        return upsert_worksheet_data(worksheet, df_hdd, keys, status_col_index=8)




    except Exception as e:




        return False, f"Loi dong bo o cung: {_format_error(e)}"
















@retry_gsheet(retries=3)
def sync_intermittent_cam(intermittent_data: list[dict], sheet_name: str = "Cam chập chờn", cred_file: str | None = None) -> tuple[bool, str]:
    """Sync intermittent / recovered cameras to worksheet 'Cam chập chờn'."""
    if not intermittent_data:
        return True, "Không có dữ liệu cam chập chờn để đồng bộ"
    try:
        client = get_client(cred_file)
        sh = client.open_by_key(TARGET_SPREADSHEET_ID)
        
        target_name = (sheet_name or "Cam chập chờn").strip()
        ws = next((w for w in sh.worksheets() if w.title.strip().lower() == target_name.lower()), None)
        
        headers = ["Mã shop", "Tên shop", "Vùng", "Camera", "Chu kỳ", "Thời gian phát hiện", "Trạng thái"]
        if ws is None:
            ws = sh.add_worksheet(title=target_name, rows=1000, cols=10)
            ws.update(values=[headers], range_name="A1:G1")
            
        existing_data = ws.get_all_values()
        existing_keys = set()
        if len(existing_data) > 1:
            for r in existing_data[1:]:
                if len(r) >= 5:
                    existing_keys.add((str(r[0]).strip().lower(), str(r[3]).strip().lower(), str(r[4]).strip().lower()))
                    
        new_rows = []
        for item in intermittent_data:
            m_shop = str(item.get("Mã shop", item.get("MaShop", ""))).strip()
            cam = str(item.get("Camera", item.get("ChiTiet", ""))).strip()
            cycle = str(item.get("Chu kỳ", item.get("cycle", ""))).strip()
            k = (m_shop.lower(), cam.lower(), cycle.lower())
            if k not in existing_keys:
                row = [
                    m_shop,
                    str(item.get("Tên shop", item.get("TenShop", ""))),
                    str(item.get("Vùng", item.get("Vung", ""))),
                    cam,
                    cycle,
                    str(item.get("Thời gian", item.get("time", ""))),
                    str(item.get("Trạng thái", item.get("status", "")))
                ]
                new_rows.append(row)
                existing_keys.add(k)
                
        if new_rows:
            ws.append_rows(new_rows, value_input_option="USER_ENTERED")
            return True, f"Đã ghi nhận {len(new_rows)} camera chập chờn vào sheet '{target_name}'"
            
        return True, "Các camera chập chờn đã tồn tại trên sheet"
    except Exception as e:
        return False, f"Loi dong bo cam chap chon: {_format_error(e)}"
@retry_gsheet(retries=3)




def get_region_map(cred_file: str | None = None) -> dict:




    """




    Fetch region mapping (Mã shop -> Miền) from the 'Phân công' worksheet (GID 345218638).




    Columns G to I contain Mã shop, Tên shop, Miền.




    """




    try:




        client = get_client(cred_file)




        sh = client.open_by_key(TARGET_SPREADSHEET_ID)




        # Find sheet with GID 345218638




        ws = next((w for w in sh.worksheets() if w.id == 345218638), None)




        if not ws:




            ws = sh.worksheet("Phân công")




        




        vals = ws.get_all_values()




        if not vals or len(vals) < 2:




            return {}




            




        region_map = {}




        # Columns G to I correspond to indices 6, 7, 8




        for row in vals[1:]:




            if len(row) >= 9:




                shop_code = str(row[6]).strip()




                region = str(row[8]).strip()




                if shop_code and shop_code != "" and shop_code.lower() != "nan":




                    # Normalize shop code




                    shop_code = shop_code.removesuffix(".0")




                    region_map[shop_code] = region




        return region_map




    except Exception as e:




        print(f"Error fetching region map from GSheet: {e}")




        return {}














@retry_gsheet(retries=3)




def read_ticket_sheet(sheet_name: str = SHEET_CAM_MKN, cred_file: str | None = None):




    try:




        client = get_client(cred_file)




        worksheet = _get_worksheet(client, sheet_name)




        data = worksheet.get_all_values()




        if not data or len(data) < 2:




            return False, "Sheet trong hoac khong co du lieu"




        headers = _make_unique_headers(data[0])




        return True, pd.DataFrame(data[1:], columns=headers)




    except Exception as e:




        return False, f"Loi doc GSheet: {_format_error(e)}"














@retry_gsheet(retries=3)




def write_ticket_results(results_list, sheet_name: str = SHEET_CAM_MKN, col_letter: str = "J", cred_file: str | None = None):




    try:




        client = get_client(cred_file)




        worksheet = _get_worksheet(client, sheet_name)




        return _write_column(worksheet, col_letter, results_list)




    except Exception as e:




        return False, f"Loi ghi GSheet: {_format_error(e)}"














@retry_gsheet(retries=3)




def write_created_ticket_ids(ids_list, sheet_name: str = SHEET_CAM_MKN, cred_file: str | None = None):




    try:




        client = get_client(cred_file)




        worksheet = _get_worksheet(client, sheet_name)




        return _write_column(worksheet, "G", ids_list)




    except Exception as e:




        return False, f"Loi ghi GSheet: {_format_error(e)}"














@retry_gsheet(retries=3)




def get_dashboard_data(cred_file: str | None = None):




    """




    Fetches data from all 5 sheets and returns DataFrames + aggregated stats.




    """




    try:




        client = get_client(cred_file)




        sh = client.open_by_key(TARGET_SPREADSHEET_ID)




        




        sheets = {




            "mkn": (TARGET_GID, SHEET_SUMMARY),




            "online": (TARGET_GID_ONLINE, SHEET_ONLINE),




            "playback": (TARGET_GID_PLAYBACK, SHEET_NO_DATA),




            "hdd": (TARGET_GID_HDD, SHEET_HDD),




            "dvr": (TARGET_GID_DVR, SHEET_DVR)




        }




        




        dfs = {}




        for key, (gid, fallback_name) in sheets.items():




            ws = next((w for w in sh.worksheets() if w.id == gid), None)




            if not ws:




                try: ws = sh.worksheet(fallback_name)




                except: ws = None




            




            if ws:




                vals = ws.get_all_values()




                if len(vals) > 1:




                    headers = _make_unique_headers(vals[0])




                    df = pd.DataFrame(vals[1:], columns=headers)




                    # Remove completely empty rows




                    df = df[df.apply(lambda x: x.astype(str).str.strip().str.len().sum() > 0, axis=1)]




                    dfs[key] = df




                elif len(vals) == 1:




                    headers = _make_unique_headers(vals[0])




                    dfs[key] = pd.DataFrame(columns=headers)




                else:




                    dfs[key] = pd.DataFrame()




            else:




                dfs[key] = pd.DataFrame()









        # Aggregated Stats




        total_errors = sum(len(dfs[k]) for k in ["playback", "hdd", "dvr"])




        




        def get_sheet_stats(key):




            df = dfs.get(key, pd.DataFrame())




            if df.empty: return {"total": 0, "pending": 0, "resolved": 0, "new": 0}




            




            p, r, n = 0, 0, 0




            if df.shape[1] >= 8:




                col_h = df.iloc[:, 7].astype(str).str.lower().str.strip()




                p = (col_h == "chưa xử lý").sum()




                r = (col_h == "đã xử lý").sum()




                n = (col_h == "mới phát sinh").sum()




            




            return {"total": len(df), "pending": int(p), "resolved": int(r), "new": int(n)}









        stats = {




            "playback": get_sheet_stats("playback"),




            "hdd": get_sheet_stats("hdd"),




            "dvr": get_sheet_stats("dvr"),




            "mkn_total": len(dfs["mkn"]),




            "online_total": len(dfs["online"]),




            "global_pending": sum(get_sheet_stats(k)["pending"] for k in ["playback", "hdd", "dvr"])




        }









        return True, {"dfs": dfs, "stats": stats}




    except Exception as e:




        return False, {"error": f"Loi loading dashboard: {e}"}














@retry_gsheet(retries=3)




def update_ticket_id_single(




    row_index,




    ticket_id,




    sheet_name: str = SHEET_CAM_MKN,




    cred_file: str | None = None,




    col_index: int = 6,




    created_date: str | None = None,
    preserve_existing_date: bool = True,




):




    try:




        client = get_client(cred_file)




        worksheet = _get_worksheet(client, sheet_name)




        sheet_row = row_index + 2









        # If updating Cam mkn: Ticket is at Column G (col 7, or fallback 6) and creation date is at Column H (col 8)




        if sheet_name == SHEET_CAM_MKN and col_index in [6, 7]:




            existing_date = ""
            if preserve_existing_date:
                try:
                    val = worksheet.cell(sheet_row, 8).value
                    if val and str(val).strip().lower() not in ['nan', 'none', '']:
                        existing_date = str(val).strip()
                except Exception:
                    pass

            if existing_date:
                worksheet.update_cell(sheet_row, 7, str(ticket_id))
                return True, f"Da cap nhat ticket {ticket_id} (cot G), giu nguyen ngay tao {existing_date} (cot H) dong {sheet_row}"

            if not created_date or str(created_date).strip().lower() in ['nan', 'none', '']:




                created_date = datetime.now().strftime("%d/%m/%Y")




            range_name = f"G{sheet_row}:H{sheet_row}"




            worksheet.update(values=[[str(ticket_id), str(created_date)]], range_name=range_name)




            return True, f"Da cap nhat ticket {ticket_id} (cot G) va ngay tao {created_date} (cot H) dong {sheet_row}"









        worksheet.update_cell(sheet_row, col_index, str(ticket_id))




        return True, f"Da cap nhat dong {sheet_row}"




    except Exception as e:




        return False, f"Loi update realtime: {_format_error(e)}"




@retry_gsheet(retries=3)




def update_ticket_status_by_id(ticket_results_map: dict, sheet_name: str, col_letter: str, ticket_col_index: int, cred_file: str | None = None, logger=None):




    try:




        if logger: logger("CHECK_TICKET_GSHEET_START")




        if logger: logger(f"CHECK_TICKET_GSHEET_TARGET: sheet={sheet_name}, col={col_letter}")




        




        client = get_client(cred_file)




        worksheet = _get_worksheet(client, sheet_name)




        




        # Read the ticket column to find rows




        # gspread uses 1-based indexing




        all_records = worksheet.get_all_values()




        if not all_records or len(all_records) < 2:




            if logger: logger("CHECK_TICKET_GSHEET_FAILED: Sheet is empty")




            return False, "Sheet is empty"




            




        updates = []




        for i, row in enumerate(all_records):




            if i == 0: continue # Skip header




            if len(row) >= ticket_col_index:




                ticket_id = str(row[ticket_col_index - 1]).strip()




                if ticket_id in ticket_results_map:




                    sheet_row = i + 1 # 1-based index




                    res_val = ticket_results_map[ticket_id]




                    if logger: logger(f"CHECK_TICKET_GSHEET_ROW_FOUND: ticket={ticket_id}, row={sheet_row}")




                    updates.append({




                        'range': f"{col_letter}{sheet_row}",




                        'values': [[str(res_val)]]




                    })




        




        if updates:




            if logger: logger(f"CHECK_TICKET_GSHEET_WRITE: updating {len(updates)} cells")




            worksheet.batch_update(updates)




            if logger: logger("CHECK_TICKET_GSHEET_SUCCESS")




            return True, f"Cập nhật thành công {len(updates)} dòng"




        else:




            if logger: logger("CHECK_TICKET_GSHEET_FAILED: No matching tickets found")




            return False, "Không tìm thấy ticket để cập nhật"




            




    except Exception as e:




        if logger: logger(f"CHECK_TICKET_GSHEET_FAILED: {e}")




        return False, str(e)




