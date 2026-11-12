from __future__ import annotations

import io
import os
import re
from datetime import datetime

import pandas as pd
import requests

from app.services import backend_check


def read_input_file(file_path: str) -> pd.DataFrame:
    if file_path.lower().endswith(".csv"):
        try:
            df_in = pd.read_csv(file_path, encoding="utf-8-sig")
        except Exception:
            df_in = pd.read_csv(file_path, encoding="cp1252")
    else:
        df_in = pd.read_excel(file_path)
    df_in.columns = df_in.columns.str.strip()
    return df_in


def filter_shops(df_in: pd.DataFrame, filter_options: dict) -> pd.DataFrame:
    # Column B and C by legacy convention
    col_brand_idx = 1
    col_code_idx = 2

    if len(df_in.columns) < 3:
        return pd.DataFrame()

    df_filtered = df_in[df_in.iloc[:, col_brand_idx].astype(str).str.contains("LongChau", case=False, na=False)].copy()
    s_code = df_filtered.iloc[:, col_code_idx].astype(str).str.strip()

    mask_vaccine = s_code.str.startswith("5")
    mask_lc = s_code.str.startswith("8")
    mask_hope = (~mask_vaccine) & (~mask_lc)

    parts = [df_filtered[mask_hope]]
    if filter_options.get("vaccine"):
        parts.append(df_filtered[mask_vaccine])
    if filter_options.get("lc"):
        parts.append(df_filtered[mask_lc])

    return pd.concat(parts) if parts else pd.DataFrame()


def load_known_errors_and_tickets_from_csv(url_sheet: str) -> tuple[dict[str, list], dict]:
    known_errors: dict[str, list] = {}
    known_tickets: dict = {}
    r = requests.get(url_sheet, timeout=10)
    r.raise_for_status()

    df_sheet = pd.read_csv(io.StringIO(r.content.decode("utf-8")))
    if len(df_sheet.columns) <= 3:
        return known_errors, known_tickets

    # Find column indices for Mã shop, Số Cam, and Ticket dynamically
    col_code_idx = None
    col_cam_idx = None
    col_ticket_idx = None

    for idx, c_name in enumerate(df_sheet.columns):
        c_lower = str(c_name).strip().lower()
        if c_lower in ["mã shop", "ma shop", "mashop", "shop code", "mã kho"]:
            col_code_idx = idx
        elif c_lower in ["số cam", "so cam", "cam", "camera", "danh sách cam lỗi"]:
            col_cam_idx = idx
        elif c_lower in ["ticket", "mã ticket", "ticket id", "ticket_id"]:
            col_ticket_idx = idx

    # Fallbacks based on new layout (C: Mã shop (2), E: Số cam (4), G: Ticket (6))
    if col_code_idx is None:
        col_code_idx = 2 if len(df_sheet.columns) > 2 else 0
    if col_cam_idx is None:
        col_cam_idx = 4 if len(df_sheet.columns) > 4 else 3
    if col_ticket_idx is None:
        col_ticket_idx = 6 if len(df_sheet.columns) > 6 else 5

    for _, row_s in df_sheet.iterrows():
        raw_code: str = str(row_s.iloc[col_code_idx]).strip()
        raw_code = raw_code.removesuffix(".0")

        ticket_val = ""
        if col_ticket_idx is not None and len(row_s) > col_ticket_idx:
            raw_t = str(row_s.iloc[col_ticket_idx]).strip().removesuffix(".0")
            if raw_t.lower() not in ["nan", "none", "0", ""]:
                ticket_val = raw_t

        if ticket_val:
            if raw_code not in known_tickets:
                known_tickets[raw_code] = ticket_val

        cam_errs = str(row_s.iloc[col_cam_idx]) if len(row_s) > col_cam_idx else ""
        if pd.isna(cam_errs) or cam_errs.strip() == "":
            continue

        parts = [x.strip().upper() for x in re.split(r"[,\s]+", cam_errs) if x.strip()]
        norm_list = []
        for p in parts:
            m_cam = re.match(r"^(CH|CAMERA)(\d+)$", p, re.IGNORECASE)
            if m_cam:
                num = int(m_cam.group(2))
                norm_list.append(f"CH{num:02d}")
            elif "DVR" in p or "ĐẦU" in p or "ĐẦU" in p:
                norm_list.append("DVR")
            else:
                norm_list.append(p)

        for norm_cam in norm_list:
            if ticket_val:
                known_tickets[(raw_code, norm_cam)] = ticket_val

        if raw_code in known_errors:
            known_errors[raw_code].extend(norm_list)
        else:
            known_errors[raw_code] = norm_list

    return known_errors, known_tickets


def load_known_errors_from_csv(url_sheet: str) -> dict[str, list]:
    known_errors, _ = load_known_errors_and_tickets_from_csv(url_sheet)
    return known_errors


def detect_columns(df_process: pd.DataFrame) -> dict[str, str]:
    cols = df_process.columns
    ip_col = backend_check.find_col_name(cols, ["IP", "Address"])
    if not ip_col and len(cols) >= 5:
        ip_col = cols[4]
    code_col = cols[2] if len(cols) > 2 else None
    name_col = backend_check.find_col_name(cols, ["Tên", "Name", "Shop Name"])
    return {"ip": str(ip_col), "code": str(code_col), "name": str(name_col)}


def generate_ticket_dataframe(
    results: list,
    region_file: str,
    create_data_list: list,
    known_errors: dict[str, list],
    log_fn=None,
    known_tickets: dict | None = None,
) -> dict:
    """
    Generate ticket dataframes and various report categories in a dictionary.
    """
    df_out = pd.DataFrame(results)
    import re

    # Prepare region map
    region_map = {}
    if isinstance(region_file, dict):
        region_map = region_file
    elif region_file and isinstance(region_file, str) and os.path.exists(region_file):
        try:
            df_r = pd.read_excel(region_file)
            cols = df_r.columns
            c_shop = backend_check.find_col_name(cols, ["MaShop", "Shop Code", "Mã kho", "Mã shop", "ShopID"])
            c_region = backend_check.find_col_name(cols, ["Region", "Vùng", "Khu vực", "Area", "Location"])

            if c_shop and c_region:
                for _, r_r in df_r.iterrows():
                    k = str(r_r[c_shop]).strip()
                    k = k.removesuffix(".0")
                    region_map[k] = str(r_r[c_region]).strip()
        except Exception:
            pass

    if "MaShop" in df_out.columns:
        ticket_data = []
        online_data = []
        ftel_data = []
        hdd_data = []
        playback_data = []

        df_clean = df_out.copy()

        if not df_clean.empty:
            grouped = df_clean.groupby(["MaShop", "TenShop"])

            for (shop_code, shop_name), group in grouped:
                shop_code = str(shop_code).strip()
                shop_code = shop_code.removesuffix(".0")

                curr_errors: list[str] = []
                curr_onlines: list[str] = []
                cam_status_map: dict[str, str] = {}

                for _, row in group.iterrows():
                    detail = str(row["ChiTiet"])
                    status = str(row["TrangThai"])

                    code = detail
                    # Normalize Cam Name to CHxx (recognize "Camera x" or "CHx")
                    m = re.search(r"(?:Camera\s+|CH)(\d+)", detail, re.IGNORECASE)
                    if m:
                        code = f"CH{m.group(1).zfill(2)}"
                    elif "Đầu ghi" in detail:
                        code = "DVR"

                    if code not in cam_status_map:
                        cam_status_map[code] = {
                            "status": status, 
                            "lrt": str(row.get("LastRecordTime", "")),
                            "port": str(row.get("Port_Cam_Con", ""))
                        }
                    else:
                        if "Online" in status:
                            cam_status_map[code] = {
                                "status": status, 
                                "lrt": str(row.get("LastRecordTime", "")),
                                "port": str(row.get("Port_Cam_Con", ""))
                            }

                for code, info in cam_status_map.items():
                    if "Online" in info["status"]:
                        curr_onlines.append(code)
                    else:
                        curr_errors.append(code)

                old_list: list[str] = []
                found_in_ui = False
                if create_data_list:
                    for item in create_data_list:
                        # Normalize UI shop code
                        item_shop_code = str(item.get("ma_shop", "")).strip()
                        item_shop_code = item_shop_code.removesuffix(".0")

                        if item_shop_code == shop_code:
                            found_in_ui = True
                            raw_old = str(item.get("_old_offline", ""))
                            if raw_old:
                                parts = [x.strip().upper() for x in re.split(r"[,\s]+", raw_old) if x.strip()]
                                for p in parts:
                                    m_cam = re.match(r"^(CH|CAMERA)\s*(\d+)$", p, re.IGNORECASE)
                                    if m_cam:
                                        old_list.append(f"CH{int(m_cam.group(2)):02d}")
                                    elif "DVR" in p or "ĐẦU" in p or "ĐẦU" in p:
                                        old_list.append("DVR")
                                    else:
                                        old_list.append(p)
                                found_in_ui = True
                            break

                # FALLBACK to known_errors only if not found in UI list OR UI list has no old errors
                if not old_list and not found_in_ui:
                    old_list = known_errors.get(shop_code, [])

                # 1. CLASSIFY ERRORS
                new_offline = [c for c in curr_errors if c not in old_list]
                still_offline = [c for c in curr_errors if c in old_list]

                # 2. IDENTIFY RECOVERIES (Back Online)
                scanned_cameras = any("Đầu ghi" not in str(row["ChiTiet"]) for _, row in group.iterrows())
                if scanned_cameras:
                    # Resolve: Any cam in old_list NOT currently offline is considered Recovered
                    back_online = [c for c in old_list if c not in curr_errors and c != "DVR"]
                else:
                    # DVR might be offline, fallback to strict reported online status
                    back_online = [c for c in curr_onlines if c in old_list]

                # Cleanup (Double check against onlines for safety)
                curr_errors = [c for c in curr_errors if c not in curr_onlines]
                new_offline = [c for c in new_offline if c not in curr_onlines]
                still_offline = [c for c in still_offline if c not in curr_onlines]

                # 1. CLASSIFY BY STATUS AND BRAND
                if "DVR" in curr_errors:
                    # DVR Offline
                    dvr_stat = cam_status_map.get("DVR", {}).get("status", "")
                    if "Lỗi Đầu Ghi" not in dvr_stat and "Mất mạng" not in dvr_stat:
                        ftel_data.append({
                            "Mã shop": shop_code, "Tên shop": shop_name, "Vùng": region_map.get(shop_code, ""),
                            "Chi Tiết": "Đầu ghi", "Trạng Thái": dvr_stat or "Offline"
                        })
                    curr_errors.remove("DVR")
                
                if "DVR" in curr_onlines:
                    # DVR Online - DO NOT append to ftel_data (Lỗi đầu ghi sheet)
                    # This allows upsert to mark old errors as "Resolved" (đã xử lý)
                    curr_onlines.remove("DVR")
                
                # Cleanup back_online
                back_online = [c for c in back_online if c != "DVR"]

                # 2. TICKET DATA (HIKVISION Offline Errors - Sheet "Tổng camera")
                if curr_errors:
                    for cam in sorted(set(curr_errors)):
                        # Filter out Port 554 and 80 for "Tổng camera" sheet as requested
                        port = cam_status_map.get(cam, {}).get("port", "")
                        if port in ["554", "80"]:
                            continue

                        lrt = str(cam_status_map[cam]["lrt"]).strip() if cam in cam_status_map else ""
                        days = ""
                        
                        # If no playback found or specific strings indicate long-term offline
                        if not lrt or any(x in lrt for x in ["No", "No Records", "No Data", "Cam mkn đã lâu"]):
                            days = "MKN lâu ngày"
                        elif any(x in lrt.lower() for x in ["401", "fail"]):
                            days = "MKN lâu ngày"
                        else:
                            # Try to calculate days from timestamp
                            lrt_clean = lrt.replace('T', ' ')
                            try:
                                # Try standard format: HH:MM:SS DD/MM/YYYY
                                dt = datetime.strptime(lrt_clean, "%H:%M:%S %d/%m/%Y")
                                diff = datetime.now() - dt
                                days = f"{diff.days} Ngày"
                            except:
                                try:
                                    # Fallback to secondary format: YYYY-MM-DD HH:MM
                                    dt = datetime.strptime(lrt_clean, "%Y-%m-%d %H:%M")
                                    diff = datetime.now() - dt
                                    days = f"{diff.days} Ngày"
                                except:
                                    # If parsing still fails, categorize as long-term offline/unknown
                                    days = "MKN lâu ngày"

                        ticket_data.append({
                            "Mã shop": shop_code, "Tên shop": shop_name, "Vùng": region_map.get(shop_code, ""),
                            "Danh sách Cam lỗi": cam, "Cam cũ vẫn lỗi": cam if cam in still_offline else "",
                            "Cam mới offline": cam if cam in new_offline else "", "Cam đã online": "",
                            "Số ngày offline": days
                        })

                # 3. ONLINE RECOVERIES (HIKVISION Back Online - Sheet "Cam online")
                if back_online:
                    for cam in sorted(set(back_online)):
                        # 1. Lookup Ticket
                        ticket_val = ""
                        if known_tickets:
                            ticket_val = str(known_tickets.get((shop_code, cam), "")).strip()
                            if not ticket_val:
                                ticket_val = str(known_tickets.get(shop_code, "")).strip()
                        if not ticket_val and create_data_list:
                            for item in create_data_list:
                                s_c = str(item.get("ma_shop", "")).strip().removesuffix(".0")
                                if s_c == shop_code:
                                    ticket_val = str(item.get("ticket", item.get("ticket_id", item.get("Ticket", "")))).strip()
                                    if ticket_val:
                                        break

                        # 2. Determine Online Date (Phương án A: Ngày bắt đầu có record của chu kỳ hiện tại)
                        lrt = str(cam_status_map[cam]["lrt"]).strip() if cam in cam_status_map else ""
                        shop_ip = ""
                        shop_port = 81
                        for _, r_cam in group.iterrows():
                            if str(r_cam.get("ChiTiet", "")).strip() == cam:
                                shop_ip = str(r_cam.get("IP_DauGhi", "")).strip()
                                shop_port = r_cam.get("Port", 81)
                                break
                        if not shop_ip and not group.empty:
                            shop_ip = str(group.iloc[0].get("IP_DauGhi", "")).strip()
                            shop_port = group.iloc[0].get("Port", 81)

                        online_date = ""
                        if shop_ip:
                            try:
                                dvr_ch = ""
                                for _, r_cam in group.iterrows():
                                    if str(r_cam.get("ChiTiet", "")).strip() == cam:
                                        dvr_ch = str(r_cam.get("DVR_Channel", "")).strip()
                                        break
                                online_date = backend_check.find_session_start_date(
                                    ip=shop_ip,
                                    port=shop_port,
                                    channel_name=cam,
                                    last_record_time_str=lrt,
                                    dvr_channel=dvr_ch,
                                )
                            except Exception as ex:
                                if log_fn:
                                    log_fn(f"[WARN] Lỗi xác định ngày record {shop_code} {cam}: {ex}")

                        if not online_date:
                            if lrt and not any(x in lrt.lower() for x in ["no", "401", "fail"]):
                                m_date = re.search(r"(\d{2}/\d{2}/\d{4})", lrt)
                                if m_date:
                                    online_date = m_date.group(1)
                                else:
                                    m_date_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", lrt)
                                    if m_date_iso:
                                        online_date = f"{m_date_iso.group(3)}/{m_date_iso.group(2)}/{m_date_iso.group(1)}"
                        if not online_date:
                            online_date = datetime.now().strftime("%d/%m/%Y")

                        online_data.append({
                            "Mã shop": shop_code,
                            "Tên shop": shop_name,
                            "Vùng": region_map.get(shop_code, ""),
                            "Cam đã online": cam,
                            "Ticket": ticket_val,
                            "Ngày online": online_date,
                        })

                # 3. HDD vs PLAYBACK Errors (Online but No Record / Aging > 2 Days)
                no_record_list = []
                for c in curr_onlines:
                    lrt = str(cam_status_map[c].get("lrt", "")).strip()
                    is_empty = lrt in ["No Records", "No Data", "Cam mkn đã lâu", ""]
                    days_count = ""
                    is_aged = False
                    
                    if is_empty:
                        # CASE: NO RECORDS AT ALL (Long term or overwrite)
                        days_count = "Mất playback lâu ngày"
                    elif not any(x in lrt.lower() for x in ["fail", "401"]):
                        try:
                            lrt_clean = lrt.replace('T', ' ')
                            dt = None
                            try: dt = datetime.strptime(lrt_clean, "%H:%M:%S %d/%m/%Y")
                            except: 
                                try: dt = datetime.strptime(lrt_clean, "%Y-%m-%d %H:%M")
                                except: pass
                            
                            if dt:
                                diff_days = (datetime.now() - dt).days
                                days_count = diff_days
                                if diff_days >= 2:
                                    is_aged = True
                        except: pass
                    
                    if is_empty or is_aged:
                        no_record_list.append({"cam": c, "days": days_count})
                
                if no_record_list:
                    total_cams = len(cam_status_map)
                    all_online = len(curr_onlines) == total_cams
                    all_no_record = len(no_record_list) == total_cams
                    
                    if all_online and all_no_record:
                        # CASE: HDD ERROR (All online, All no record)
                        # Consolidate to one row per shop, removing individual "Số cam"
                        max_days = ""
                        for item in no_record_list:
                            if item["days"] != "":
                                if max_days == "" or (isinstance(item["days"], int) and (max_days == "" or item["days"] > max_days)):
                                    max_days = item["days"]
                        
                        hdd_data.append({
                            "Mã shop": shop_code, "Tên shop": shop_name, "Vùng": region_map.get(shop_code, ""),
                            "Số ngày không có playback": max_days
                        })
                    else:
                        # CASE: PLAYBACK ERROR (Individual online cam with no record)
                        for item in no_record_list:
                            playback_data.append({
                                "Mã shop": shop_code, "Tên shop": shop_name, "Vùng": region_map.get(shop_code, ""),
                                "Số cam": item["cam"], "Số ngày không có playback": item["days"]
                            })

            results_dict = {
                "df_ticket": pd.DataFrame(ticket_data),
                "df_out": df_out,
                "df_online": pd.DataFrame(online_data),
                "df_ftel": pd.DataFrame(ftel_data),
                "df_hdd": pd.DataFrame(hdd_data),
                "df_playback": pd.DataFrame(playback_data)
            }
            return results_dict
    return {}
import typing
import pandas as pd
import re

def generate_camera_export_excel(dfs: dict, fpath: str):
    df_out = dfs.get("df_out", pd.DataFrame())
    df_ticket = dfs.get("df_ticket", pd.DataFrame())
    df_online = dfs.get("df_online", pd.DataFrame())
    df_ftel = dfs.get("df_ftel", pd.DataFrame())
    df_hdd = dfs.get("df_hdd", pd.DataFrame())
    df_playback = dfs.get("df_playback", pd.DataFrame())

    if not isinstance(df_out, pd.DataFrame) or df_out.empty:
        raise ValueError("No data to export")

    column_order = [
        'MaShop', 'TenShop', 'IP_DauGhi', 
        'ChiTiet', 'IP_Cam_Con', 'Port_Cam_Con', 'TrangThai', 'LastRecordTime', 'GhiChu'
    ]
    
    rename_map = {
        "MaShop": "MaShop", "TenShop": "TenShop", "IP_DauGhi": "IP_DauGhi",
        "ChiTiet": "ChiTiet", "IP_Cam_Con": "IP_Cam_Con", "Port_Cam_Con": "Port_Cam_Con",
        "TrangThai": "TrangThai", "GhiChu": "GhiChu"
    }
    
    def format_df_safe(df_input: typing.Any) -> typing.Any:
        if not isinstance(df_input, pd.DataFrame) or df_input.empty:
            return pd.DataFrame()
        dfr = df_input.rename(columns=rename_map)
        exist = [c for c in column_order if c in dfr.columns]
        return dfr[exist]

    # 4. SPLIT by Shop Type
    s_mashop = df_out['MaShop'].astype(str).str.strip()
    df_vaccine = df_out[s_mashop.str.startswith('5')].copy()
    df_lc = df_out[s_mashop.str.startswith('8')].copy()
    df_hope = df_out[(~s_mashop.str.startswith('5')) & (~s_mashop.str.startswith('8'))].copy()

    def simplify_status_safe(val: typing.Any) -> str:
        s = str(val)
        if 'Analog' in s or 'Dòng khác' in s:
            return s
        return 'Online' if 'Online' in s else 'Offline'

    for dfr_any in [df_vaccine, df_lc, df_hope]:
         if isinstance(dfr_any, pd.DataFrame) and not dfr_any.empty:
             dfr_any['TrangThai'] = dfr_any['TrangThai'].apply(simplify_status_safe)

    with pd.ExcelWriter(fpath, engine='openpyxl') as writer:
        # Sheet 1 & 2: Ticket Summary & GSheet Data
        df_sync = df_ticket.copy()
        if not df_ticket.empty:
            df_sync = df_ticket[df_ticket['Danh sách Cam lỗi'].astype(str) != "DVR"].copy()
            cols_to_drop = ['Cam đã online', 'Cam cũ vẫn lỗi']
            df_sync = df_sync.drop(columns=[c for c in cols_to_drop if c in df_sync.columns])
            
            day_col = "Số ngày offline"
            if day_col in df_sync.columns:
                def sort_key(val):
                    s = str(val).strip().lower()
                    if "lâu ngày" in s or "lâu" in s: return 9999
                    try: return int(re.sub(r'\D', '', s))
                    except: return 0
                df_sync['__sorted__'] = df_sync[day_col].apply(sort_key)
                df_sync = df_sync.sort_values(by='__sorted__', ascending=False).drop(columns=['__sorted__'])

        df_sync.to_excel(writer, sheet_name='Tổng Camera', index=False)
        df_online.to_excel(writer, sheet_name='Cam online', index=False)
        df_ftel.to_excel(writer, sheet_name='Đầu ghi Ftel', index=False)
        df_hdd.to_excel(writer, sheet_name='lỗi ổ cứng', index=False)
        df_playback.to_excel(writer, sheet_name='cam không có playback', index=False)
        
        for df_part, s_name in [(df_vaccine, 'Vaccine'), (df_lc, 'Long Châu'), (df_hope, 'HOPE')]:
            fmt = format_df_safe(df_part)
            fmt.to_excel(writer, sheet_name=s_name, index=False)



