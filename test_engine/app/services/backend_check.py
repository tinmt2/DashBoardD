import logging
import platform
import socket
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import pandas as pd  # type: ignore
import requests  # type: ignore
from requests.auth import HTTPBasicAuth, HTTPDigestAuth  # type: ignore

from app.config import get_config  # type: ignore

# --- CẤU HÌNH (CONFIGURATION) ---
MIN_CYCLE_TIME = 120 # Cycle time for monitoring in seconds
MAX_WORKERS = 30
TIMEOUT = 15
SCAN_PORTS = [81, 82]  # Scan ports 81 and 82
PING_RETRIES = 5
TIMEOUT_PING = 15.0

# TODO: Cập nhật danh sách user/pass thực tế nếu cần.
# List of (username, password) tuples
HIK_CREDS = [
    ('monitor', 'frt2012;;'),
]

try:
    from ping3 import ping  # type: ignore
except ImportError:
    ping = None

logger = logging.getLogger("hik_playback")
AUTH_FAIL = "__AUTH_FAIL__"

import threading
_thread_local = threading.local()
STOP_FLAGS = {}
_stop_lock = threading.Lock()

def set_current_job_id(job_id: str):
    _thread_local.job_id = job_id

def is_stopped(job_id: str = None) -> bool:
    jid = job_id or getattr(_thread_local, "job_id", None)
    if not jid: return False
    with _stop_lock: return STOP_FLAGS.get(jid, False)

def signal_stop(job_id: str):
    with _stop_lock: STOP_FLAGS[job_id] = True
    logger.info(f">>> STOP SIGNAL RECEIVED FOR JOB {job_id} <<<")

def signal_start(job_id: str):
    with _stop_lock: STOP_FLAGS[job_id] = False
    
def clear_stop(job_id: str):
    with _stop_lock:
        if job_id in STOP_FLAGS: del STOP_FLAGS[job_id]

# =================================================================================
# UTILITIES
# =================================================================================

def ping_ip(ip):
    """
    Robust ping check:
    1. Try ping3 (if installed).
    2. Fallback to system ping command (subprocess).
    """
    for i in range(PING_RETRIES):
        # 1. ping3
        try:
            if ping and ping(ip, timeout=TIMEOUT_PING, unit='ms'): 
                return True
        except: 
            pass
        
        # 2. Subprocess Fallback
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            # Windows flag to hide window
            creationflags = 0x08000000 if platform.system().lower() == 'windows' else 0
            
            wait_ms = str(int(TIMEOUT_PING * 1000))
            command = ['ping', param, '1', '-w', wait_ms, ip]
            
            startupinfo = None
            if platform.system().lower() == 'windows':
                startupinfo = subprocess.STARTUPINFO() # type: ignore
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW # type: ignore
                
            result = subprocess.call(
                command, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, 
                startupinfo=startupinfo, 
                creationflags=creationflags
            )
            if result == 0:
                return True
        except: 
            pass
        
        time.sleep(0.2)
    return False

def check_port(ip, port):
    """Check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT) 
        res = sock.connect_ex((str(ip), int(port)))
        sock.close()
        return res == 0
    except: 
        return False

def find_col_name(columns, keywords):
    """Find a column name containing any of the keywords."""
    for col in columns:
        for kw in keywords:
            if kw.lower() in str(col).lower(): return col
    return None

# =================================================================================
# HIKVISION API LOGIC
# =================================================================================

def smart_find(element, tag_name):
    if element is None: return ""
    for child in element.iter():
        if child.tag.endswith(tag_name) and child.text:
            return child.text.strip()
    return ""

def parse_xml_safe(text):
    try:
        return ET.fromstring(text.replace('xmlns="http://www.hikvision.com/ver20/XMLSchema"', ''))
    except Exception:
        return None


def _fetch_api(base_url, path, auth_digest, auth_basic, timeout=TIMEOUT):
    headers = {"X-Requested-With": "XMLHttpRequest"}
    try:
        r = requests.get(base_url + path, auth=auth_digest, headers=headers, timeout=timeout)
        if r.status_code == 401:
            logger.warning("api GET %s returned 401 with digest, trying basic", path)
            r = requests.get(base_url + path, auth=auth_basic, headers=headers, timeout=timeout)
        
        if r.status_code == 200:
            return parse_xml_safe(r.text)
        else:
            if not is_stopped():
                logger.warning("api GET %s failed status=%s text=%s", path, r.status_code, r.text[:100])
    except Exception as e:
        logger.error("api GET %s exception: %s", path, e)
    return None


def _get_record_tracks(base_url, auth_digest, auth_basic):
    path = "/ISAPI/ContentMgmt/record/tracks"
    # Try fetching with standard fetch_api first
    root = _fetch_api(base_url, path, auth_digest, auth_basic)
    if root is None:
        # If fetch_api failed, it already logged warnings. 
        # But we need to specify if it was specifically an AUTH failure (401)
        try:
            headers = {"X-Requested-With": "XMLHttpRequest"}
            r = requests.get(base_url + path, auth=auth_digest, headers=headers, timeout=TIMEOUT)
            if r.status_code == 401:
                r = requests.get(base_url + path, auth=auth_basic, headers=headers, timeout=TIMEOUT)
            
            if r.status_code == 401:
                logger.error("CRITICAL: tracks auth failed for %s", base_url)
                return {}, True
            logger.warning("tracks request failed for %s status=%s", base_url, r.status_code)
        except Exception:
            logger.exception("tracks connection failure")
        return {}, False

    track_map = {}
    for elem in root.iter():
        if elem.tag.endswith("track"):
            track_id = None
            channel_id = None
            for child in elem:
                if child.tag.endswith("trackID"):
                    t_text = child.text
                    if t_text is not None:
                        track_id = t_text.strip()
                elif child.tag.endswith("channelID") or child.tag.endswith("channel"):
                    c_text = child.text
                    if c_text is not None:
                        channel_id = str(c_text).strip()
            if track_id:
                track_map[track_id] = channel_id

    if track_map:
        logger.info("tracks found=%s map=%s", len(track_map), track_map)
    else:
        logger.warning("tracks empty")
    return track_map, False



def _guess_track_ids(channel_id: str):
    cid = str(channel_id).strip()
    if not cid.isdigit():
        return []
    # Common Hikvision patterns: 101/102 for ch1, 201/202 for ch2...
    return [f"{cid}01", f"{cid}02", f"{cid}1", f"{cid}2", f"{cid}"]


def _search_last_record_time(base_url, auth_digest, auth_basic, track_id, days=7, use_local_time=False):
    cfg = get_config()
    playback_cfg = cfg.get("check_cam", {})
    end_margin_hours = float(playback_cfg.get("playback_end_margin_hours", 0))
    debug_ip = playback_cfg.get("playback_debug_ip", "")
    debug_max = int(playback_cfg.get("playback_debug_max", 1))

    if use_local_time:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        end_time = end_time + timedelta(hours=end_margin_hours)
        start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
        end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')
    else:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        end_time = end_time + timedelta(hours=end_margin_hours)
        start_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    search_id = str(uuid.uuid4()).upper()
    
    def do_search(position: int, max_results: int):
        # Mirroring web UI: using BOTH correct and typo'd position tags to ensure compatibility.
        # Also using <trackList> instead of <trackIDList> and the web UI's metadata descriptor.
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CMSearchDescription version="1.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <searchID>{search_id}</searchID>
  <trackList>
    <trackID>{track_id}</trackID>
  </trackList>
  <timeSpanList>
    <timeSpan>
      <startTime>{start_str}</startTime>
      <endTime>{end_str}</endTime>
    </timeSpan>
  </timeSpanList>
  <maxResults>{max_results}</maxResults>
  <searchResultPosition>{position}</searchResultPosition>
  <searchResultPostion>{position}</searchResultPostion>
</CMSearchDescription>
"""
        # Mirroring web UI header which sometimes helps with 401/403
        headers = {
            "Content-Type": "application/xml",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        try:
            if is_stopped(): return None
            r = requests.post(base_url + "/ISAPI/ContentMgmt/search", data=xml, headers=headers, auth=auth_digest, timeout=TIMEOUT)
            if r.status_code == 401:
                 if is_stopped(): return None
                 r = requests.post(base_url + "/ISAPI/ContentMgmt/search", data=xml, headers=headers, auth=auth_basic, timeout=TIMEOUT)
            
            if debug_ip and debug_ip in base_url and debug_max > 0:
                try:
                    from app.paths import RUNTIME_DIR  # type: ignore
                    fname = RUNTIME_DIR / f"hik_search_{debug_ip.replace('.', '_')}_{track_id}_{position}.xml"
                    with open(fname, "w", encoding="utf-8") as f:
                        f.write(xml + "\n\n" + r.text)
                    playback_cfg["playback_debug_max"] = debug_max - 1
                except Exception: pass
            return r
        except Exception as e:
            logger.error("search request error: %s", e)
            return None

    # Removed recursive Recent Search to avoid redundant calls on slow devices.
    # The calling function (get_hik_details) should manage tiered search logic.

    found_times = []
    total_matches = 0
    debug_shop_match = False # Will be set by caller if needed

    try:
        if is_stopped(): return None
        # STEP 1: Get total count using maxResults=1
        if not is_stopped():
            logger.info("[SEARCH] track=%s window_days=%s startTime=%s endTime=%s", track_id, days, start_str, end_str)
        r = do_search(position=0, max_results=1)
        if r is None: return None
        
        if r.status_code != 200:
            if r.status_code == 401:
                return AUTH_FAIL
            return None
        
        root = parse_xml_safe(r.text)
        if root is not None:
            total_matches_val = None
            num_of_matches_val = None
            for elem in root.iter():
                tag = elem.tag.lower()
                if tag.endswith("totalmatches"):
                    if elem.text:
                        try:
                            total_matches_val = int(str(elem.text).strip())
                        except: pass
                elif tag.endswith("numofmatches"):
                    if elem.text:
                        try:
                            num_of_matches_val = int(str(elem.text).strip())
                        except: pass
            
            if total_matches_val is not None:
                extracted_total = total_matches_val
            elif num_of_matches_val is not None:
                extracted_total = num_of_matches_val
            else:
                extracted_total = 0
            
            total_matches = extracted_total
            logger.info("[RESULT] track=%s totalMatches_raw=%s numOfMatches_raw=%s parsed_totalMatches=%s maxResults=1 position=0", track_id, total_matches_val, num_of_matches_val, total_matches)
            
            # Extract times from the first result if any
            first_times = _extract_match_times(root)
            found_times.extend(first_times)
            if first_times:
                logger.info("[RESULT] track=%s position=0 found times: %s", track_id, first_times)
            
            # STEP 2: Fetch the LAST record if total > 1
            if total_matches > 1:
                if is_stopped(): return None
                last_pos = int(total_matches) - 1
                logger.info("[SEARCH] track=%s Fetching last position: %s", track_id, last_pos)
                r_last = do_search(position=last_pos, max_results=1)
                if r_last and r_last.status_code == 200:
                    root_last = parse_xml_safe(r_last.text)
                    if root_last:
                        last_times = _extract_match_times(root_last)
                        found_times.extend(last_times)
                        logger.info("[RESULT] track=%s position=%s found times: %s", track_id, last_pos, last_times)

    except Exception as e:
        logger.exception("search composite logic failed: %s", e)
        return None

    # Pick the absolute latest from all sampled candidates
    latest = _pick_latest_ts(found_times)
    logger.info("[RESULT] track=%s latest_in_window=%s", track_id, latest)
    return latest


def find_session_start_date(
    ip: str,
    port: int | str = 81,
    channel_name: str = "CH01",
    last_record_time_str: str = "",
    use_local_time: bool | None = None,
    max_days: int = 14, dvr_channel: str = "",
) -> str:
    """
    Find the date when the camera first started recording in the current continuous session
    (Phương án A: Day when recording resumed after an offline gap).
    """
    import re
    if is_stopped():
        return datetime.now().strftime("%d/%m/%Y")

    # 1. Parse reference datetime from last_record_time_str
    ref_dt = None
    if last_record_time_str:
        clean_ts = str(last_record_time_str).replace("T", " ").strip()
        for fmt in (
            "%H:%M:%S %d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
        ):
            try:
                ref_dt = datetime.strptime(clean_ts, fmt)
                break
            except Exception:
                pass
    if not ref_dt:
        ref_dt = datetime.now()

    current_date = ref_dt.date()
    session_start_date = current_date

    if not ip:
        return session_start_date.strftime("%d/%m/%Y")

    if use_local_time is None:
        cfg = get_config()
        use_local_time = bool(cfg.get("check_cam", {}).get("playback_use_local_time", False))

    # 2. Extract channel ID
    if dvr_channel:
        cid = str(dvr_channel).strip()
    else:
        m = re.search(r"\d+", str(channel_name))
        cid = str(int(m.group(0))) if m else "1"

    base_url = f"http://{ip}:{port}"
    headers = {
        "Content-Type": "application/xml",
        "X-Requested-With": "XMLHttpRequest",
    }

    for user, pwd in HIK_CREDS:
        if is_stopped():
            break
        auth_digest = HTTPDigestAuth(user, pwd)
        auth_basic = HTTPBasicAuth(user, pwd)

        try:
            track_map, auth_fail = _get_record_tracks(base_url, auth_digest, auth_basic)
            if auth_fail:
                continue

            track_id = None
            for t_id, ch_id in track_map.items():
                if ch_id and str(ch_id).strip() == str(cid).strip():
                    track_id = t_id
                    break
            if not track_id:
                candidate_ids = _guess_track_ids(cid)
                track_id = candidate_ids[0] if candidate_ids else f"{cid}01"

            # Check day by day backwards
            for k in range(1, max_days + 1):
                if is_stopped():
                    break
                target_date = current_date - timedelta(days=k)
                if use_local_time:
                    start_str = target_date.strftime("%Y-%m-%dT00:00:00")
                    end_str = target_date.strftime("%Y-%m-%dT23:59:59")
                else:
                    start_str = target_date.strftime("%Y-%m-%dT00:00:00Z")
                    end_str = target_date.strftime("%Y-%m-%dT23:59:59Z")

                search_id = str(uuid.uuid4()).upper()
                xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<CMSearchDescription version="1.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <searchID>{search_id}</searchID>
  <trackList>
    <trackID>{track_id}</trackID>
  </trackList>
  <timeSpanList>
    <timeSpan>
      <startTime>{start_str}</startTime>
      <endTime>{end_str}</endTime>
    </timeSpan>
  </timeSpanList>
  <maxResults>1</maxResults>
  <searchResultPosition>0</searchResultPosition>
</CMSearchDescription>
"""
                r = requests.post(base_url + "/ISAPI/ContentMgmt/search", data=xml, headers=headers, auth=auth_digest, timeout=TIMEOUT)
                if r is not None and r.status_code == 401:
                    r = requests.post(base_url + "/ISAPI/ContentMgmt/search", data=xml, headers=headers, auth=auth_basic, timeout=TIMEOUT)

                if r is not None and r.status_code == 200:
                    root = parse_xml_safe(r.text)
                    total_m = 0
                    if root is not None:
                        for elem in root.iter():
                            tag = elem.tag.lower()
                            if tag.endswith("totalmatches") or tag.endswith("numofmatches"):
                                if elem.text:
                                    try:
                                        total_m = int(str(elem.text).strip())
                                    except Exception:
                                        pass
                    if total_m > 0:
                        session_start_date = target_date
                    else:
                        break
                else:
                    break

            return session_start_date.strftime("%d/%m/%Y")
        except Exception as e:
            logger.warning("find_session_start_date error for %s track %s: %s", base_url, cid, e)
            break

    return session_start_date.strftime("%d/%m/%Y")


def _parse_iso_ts(ts: str, force_naive=False):
    if not ts:
        return None
    try:
        # Hikvision often suffixes 'Z' but provides Local Time strings.
        # If force_naive is true, we strip the Z to avoid timezone conversion in astimezone().
        if ts.endswith("Z"):
            if force_naive:
                ts = ts.replace("Z", "")
            else:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        
        ts = ts.replace(" ", "T")
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _pick_latest_ts(ts_list, force_naive=False):
    if not ts_list:
        return None
    
    valid_pairs = []
    for ts in ts_list:
        dt = _parse_iso_ts(ts, force_naive=force_naive)
        if dt is not None:
            # For sorting, ensure all are naive or all are aware.
            # If we have a mix, we treat naive as "local" (system local).
            # But the simplest is to convert to a common baseline for comparison.
            sort_dt = dt
            if dt.tzinfo is not None:
                sort_dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            valid_pairs.append((sort_dt, ts))
    
    if not valid_pairs:
        return None
        
    # Sort pairs by the normalized datetime
    valid_pairs.sort(key=lambda x: x[0])
    # The last element in the sorted list is the latest
    return valid_pairs[-1][1]


def _extract_match_times(root):
    """
    Extract start/end times only from search match entries, not from query criteria.
    """
    times = []
    if root is None:
        return times
    # Preferred: searchMatchList/searchMatch/timeSpan
    for sm in root.iter():
        if sm.tag.endswith("searchMatch"):
            for child in sm.iter():
                if child.tag.endswith("startTime") or child.tag.endswith("endTime"):
                    if child.text:
                        times.append(child.text.strip())
    if times:
        return times
    # Fallback: look for "matchList" sections
    for ml in root.iter():
        if ml.tag.endswith("matchList"):
            for child in ml.iter():
                if child.tag.endswith("startTime") or child.tag.endswith("endTime"):
                    if child.text:
                        times.append(child.text.strip())
    return times


def _format_ts_local(ts: str, force_naive=False):
    if force_naive:
        dt_naive = _parse_iso_ts(ts, force_naive=True)
        if dt_naive: return dt_naive.strftime("%H:%M:%S %d/%m/%Y")

    # For display, we first try parsing as UTC-aware. 
    # But if the result is in the future relative to UTC-now, it's likely a pseudo-UTC.
    dt_aware = _parse_iso_ts(ts, force_naive=False)
    if dt_aware and dt_aware.tzinfo:
        now_utc = datetime.now(timezone.utc)
        # If the timestamp is more than 1 hour in the future relative to UTC, 
        # it's almost certainly shifted local time (e.g. +7).
        if dt_aware > now_utc + timedelta(hours=1):
             logger.warning("Timestamp %s appears to be pseudo-UTC (in future relative to UTC), stripping Z", ts)
             dt_naive = _parse_iso_ts(ts, force_naive=True)
             if dt_naive: return dt_naive.strftime("%H:%M:%S %d/%m/%Y")

    dt = _parse_iso_ts(ts, force_naive=False)
    if dt is None:
        return ts
    try:
        # If naive, just return as is. If aware, convert to system local.
        if dt.tzinfo:
            local_dt = dt.astimezone()
            return local_dt.strftime("%H:%M:%S %d/%m/%Y")
        return dt.strftime("%H:%M:%S %d/%m/%Y")
    except Exception:
        return ts


def get_hik_details(ip, port, user, pwd, shop_info):
    base_url = f"http://{ip}:{port}"
    auth_digest = HTTPDigestAuth(user, pwd)
    auth_basic = HTTPBasicAuth(user, pwd)

    def fetch_api(path):
        return _fetch_api(base_url, path, auth_digest, auth_basic)

    # Detect Pseudo-UTC (Z suffix on Local Time)
    device_is_pseudo_utc = False
    try:
        # Try multiple tags to be safe
        root_time = fetch_api("/ISAPI/System/time")
        sys_time = None
        if root_time is not None:
            # Try finding localTime, currentTime, or any date-like string
            sys_time = smart_find(root_time, "localTime")
            if not sys_time: sys_time = smart_find(root_time, "currentTime")
            if not sys_time:
                for elem in root_time.iter():
                    t = elem.text
                    if t is not None and ("T" in t or ":" in t):
                        sys_time = str(t).strip()
                        break
        
        if sys_time:
            # Remove Z and parse numerals
            clean_time = sys_time.replace("Z", "").replace(" ", "T").split(".")[0]
            try:
                dt_naive = datetime.fromisoformat(clean_time)
                now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                diff_hours = (dt_naive - now_utc_naive).total_seconds() / 3600
                
                logger.debug("device %s timezone check: naive=%s, utc_now=%s, diff=%.2fh", 
                               ip, dt_naive, now_utc_naive, diff_hours)
                
                # In Vietnam (+7), if diff is around 7h, it's definitely Pseudo-UTC
                if 5.0 <= diff_hours <= 9.0:
                    logger.warning("Device %s PRE-IDENTIFIED as Pseudo-UTC device. Applying +7h correction.", ip)
                    device_is_pseudo_utc = True
            except: pass
    except Exception as e:
        logger.debug("Pseudo-UTC check error for %s: %s", ip, e)

    # Lấy Config (IP, Port)
    root_config = fetch_api("/ISAPI/ContentMgmt/InputProxy/channels")
    if root_config is None:
        root_config = fetch_api("/ISAPI/System/Video/inputs/channels/status")
        if root_config is None: return None

    cam_data = {}
    items = [elem for elem in root_config.iter() if elem.tag.endswith('InputProxyChannel') or elem.tag.endswith('VideoInputChannelStatus')]
    
    for ch in items:
        cid = smart_find(ch, 'id')
        if not cid: continue
        ip_val = smart_find(ch, 'ipAddress')
        port_val = smart_find(ch, 'managePortNo')
        online_tag = smart_find(ch, 'online')
        
        cam_data[cid] = {
            "ip": ip_val if ip_val else "Analog/Unknown",
            "port": port_val,
            "status": "Online" if online_tag.lower() == 'true' else "Offline" if online_tag else "Unknown"
        }

    # Nếu chưa có status, gọi thêm API Status
    if any(v['status'] == 'Unknown' for v in cam_data.values()):
        root_status = fetch_api("/ISAPI/ContentMgmt/InputProxy/channels/status")
        if root_status is not None:
            status_items = [elem for elem in root_status.iter() if elem.tag.endswith('InputProxyChannelStatus')]
            for ch in status_items:
                cid = smart_find(ch, 'id')
                online_tag = smart_find(ch, 'online')
                if cid in cam_data and online_tag:
                     cam_data[cid]['status'] = "Online" if online_tag.lower() == 'true' else "Offline"
    
    cfg = get_config()
    playback_cfg = cfg.get("check_cam", {})
    enable_playback = playback_cfg.get("enable_playback_last_time", False)
    playback_days = int(playback_cfg.get("playback_days", 7))
    use_local_time = bool(playback_cfg.get("playback_use_local_time", False))

    track_map = {}
    tracks_auth_failed = False
    if enable_playback:
        track_map, tracks_auth_failed = _get_record_tracks(base_url, auth_digest, auth_basic)

    results = []
    for idx, (cid, data) in enumerate(cam_data.items(), start=1):
        final_status = data['status']
        if final_status == "Unknown": final_status = "Info Found"
        
        # Normalize Cam Name to CHxx sequentially from top to bottom (CH01, CH02, ...)
        cam_name = f"CH{idx:02d}"

        last_record_time = None
        if enable_playback:
            if tracks_auth_failed:
                last_record_time = "401 Unauthorized"
                results.append({
                    "MaShop": shop_info.get("code", ""),
                    "TenShop": shop_info.get("name", ""),
                    "IP_DauGhi": ip,
                    "Brand": "HIKVISION",
                    "Port": port,
                    "ChiTiet": cam_name,
                    "DVR_Channel": str(cid),
                    "IP_Cam_Con": data["ip"],
                    "Port_Cam_Con": data["port"],
                    "TrangThai": final_status,
                    "LastRecordTime": last_record_time or "",
                    "GhiChu": f"User: {user}",
                    "PhanLoai": "NORMAL",
                })
                continue
            # Try to map channel id -> trackID
            track_id = None
            for t_id, ch_id in track_map.items():
                if ch_id and str(ch_id).strip() == str(cid).strip():
                    track_id = t_id
                    break
            if not track_id:
                # Heuristic: trackID 101 => channel 1, 201 => channel 2
                try:
                    guess = int(cid)
                    for t_id in track_map.keys():
                        try:
                            t_int = int(str(t_id))
                            if t_int // 100 == guess:
                                track_id = t_id
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
            # Always include guessed tracks to ensure sub-streams (e.g. 802) are checked
            # even if track_map only explicitly listed the main stream (801).
            # Guess tracks based on the mapped track_id (e.g. 801 -> 802)
            # AND the internal cid just in case.
            candidate_ids = []
            if track_id:
                candidate_ids.append(track_id)
                # If mapped track is 801, we want to guess 802
                t_str = str(track_id).strip()
                if t_str.endswith("01"):
                    candidate_ids.append(t_str[:-2] + "02")
                elif t_str.endswith("1"):
                    candidate_ids.append(t_str[:-1] + "2")
            
            for g in _guess_track_ids(cid):
                if g not in candidate_ids:
                    candidate_ids.append(g)

            logger.info("[CHECK] shop=%s camera=%s dvr_channel=%s", shop_info.get('code', ''), cam_name, cid)
            logger.info("[TRACK] mapped=%s candidates=%s", track_id, candidate_ids)

            found_times = []
            for t_id in candidate_ids:
                if is_stopped(): break
                
                search_windows = [1]
                if playback_days > 1: search_windows.append(playback_days)
                if 60 not in search_windows: search_windows.append(60)
                
                lrt = None
                for sw_days in search_windows:
                    if is_stopped(): break
                    
                    if sw_days > 1:
                         logger.info("Camera %s/Track %s: No records in smaller windows, trying %d days...", cid, t_id, sw_days)
                         
                    lrt = _search_last_record_time(base_url, auth_digest, auth_basic, t_id, days=sw_days, use_local_time=use_local_time)
                    
                    if lrt == AUTH_FAIL:
                        last_record_time = "401 Unauthorized"
                        break
                    
                    if lrt:
                        break
                
                if last_record_time == "401 Unauthorized":
                    break
                
                if lrt:
                    found_times.append(lrt)
                    
                    dt_check = _parse_iso_ts(lrt, force_naive=True)
                    if dt_check:
                        now_naive = datetime.now()
                        if (now_naive - dt_check).total_seconds() < 48 * 3600:
                            logger.info("[PICK] Track %s returned recent enough result. Breaking.", t_id)
                            break
                    
                    if not device_is_pseudo_utc:
                        dt_aware = _parse_iso_ts(lrt, force_naive=False)
                        if dt_aware and dt_aware.tzinfo:
                            now_utc = datetime.now(timezone.utc)
                            if dt_aware > now_utc + timedelta(hours=1):
                                device_is_pseudo_utc = True
            
            logger.info("[PICK] All found_times=%s", found_times)
            if last_record_time != "401 Unauthorized":
                if found_times:
                    best_raw = _pick_latest_ts(found_times, force_naive=device_is_pseudo_utc)
                    logger.info("[PICK] best_raw selected=%s", best_raw)
                    if best_raw:
                        last_record_time = _format_ts_local(best_raw, force_naive=device_is_pseudo_utc)
                    else:
                        last_record_time = "Cam mkn đã lâu"
                else:
                    last_record_time = "Cam mkn đã lâu"
            
            logger.info("[FINAL] online_date=%s", last_record_time)
            
            logger.info("[BACKEND_RESULT]\nshop=%s\nchannel=%s\ntrack=%s\nraw_latest_timestamp=%s\nnormalized_timestamp=%s\nonline_date=%s",
                shop_info.get('code', ''), cam_name, track_id,
                locals().get('best_raw', 'None'),
                locals().get('last_record_time_str', 'None'),
                last_record_time)

        results.append({
            "MaShop": shop_info.get('code', ''),
            "TenShop": shop_info.get('name', ''),
            "IP_DauGhi": ip,
            "Brand": "HIKVISION",
            "Port": port,
            "ChiTiet": cam_name,
            "DVR_Channel": str(cid),
            "IP_Cam_Con": data['ip'],
            "Port_Cam_Con": data['port'],
            "TrangThai": final_status,
            "LastRecordTime": last_record_time or "",
            "GhiChu": f"User: {user}",
            "PhanLoai": "NORMAL"
        })
    return results

# =================================================================================
# MAIN PROCESSING LOGIC
# =================================================================================


def process_single_ip(row, col_map):
    if is_stopped(): return []
    """
    Xử lý check 1 IP (Đầu ghi).
    Trả về list danh sách camera con hoặc trạng thái đầu ghi.
    """
    ip_raw = row[col_map['ip']]
    # Ensure shop_code is stripped
    shop_code = str(row[col_map['code']]).strip() if col_map['code'] and pd.notna(row[col_map['code']]) else ""
    shop_name = str(row[col_map['name']]) if col_map['name'] and pd.notna(row[col_map['name']]) else ""
    shop_info = {'code': shop_code, 'name': shop_name}

    if pd.isna(ip_raw) or str(ip_raw).strip() == "": return []
    ip = str(ip_raw).strip()
    
    active_port = None
    brand_detected = 'UNKNOWN'
    
    # Check Ports
    for port in SCAN_PORTS:
        try:
            url = f"http://{ip}:{port}/"
            res = requests.get(url, timeout=TIMEOUT)
            active_port = port
            headers = str(res.headers).lower()
            content = res.text.lower()
            if 'hikvision' in headers or 'app-webs' in headers or '/doc/page/login.asp' in content:
                brand_detected = 'HIK'
            break 
        except Exception:
            continue

    # Case 1: Port Closed
    if active_port is None:
        is_ping_ok = ping_ip(ip)
        base_res = {
            "MaShop": shop_code, "TenShop": shop_name,
            "IP_DauGhi": ip, "Brand": "UNKNOWN", "Port": "Closed",
            "ChiTiet": "Đầu ghi", "IP_Cam_Con": "", "Port_Cam_Con": "",
            "TrangThai": "Lỗi Đầu Ghi" if is_ping_ok else "Mất mạng",
            "GhiChu": "Ping OK (Port 81 Closed)" if is_ping_ok else "Ping Timeout",
            "PhanLoai": "DAU_GHI_MKN" if is_ping_ok else "SHOP_MAT_MANG"
        }
        return [base_res]


    if brand_detected == 'HIK':
        for user, pwd in HIK_CREDS:
            details = get_hik_details(ip, active_port, user, pwd, shop_info)
            if details: return details
        
        # Login Failed
        return [{
            "MaShop": shop_code, "TenShop": shop_name,
            "IP_DauGhi": ip, "Brand": "HIKVISION", "Port": active_port,
            "ChiTiet": "Đầu ghi Hik", "IP_Cam_Con": "", "Port_Cam_Con": "",
            "TrangThai": "Sai Pass", "GhiChu": "Login failed", "PhanLoai": "NORMAL"
        }]
    else:
        # Port Open but NOT HIK
        return [{
            "MaShop": shop_code, "TenShop": shop_name,
            "IP_DauGhi": ip, "Brand": "OTHER", "Port": active_port,
            "ChiTiet": "Đầu ghi", "IP_Cam_Con": "", "Port_Cam_Con": "",
            "TrangThai": "Lỗi Đầu Ghi", "GhiChu": "Port 81 open, not HIK", "PhanLoai": "NORMAL"
        }]
    
    return []

# =================================================================================
# DVR MONITOR LOGIC
# =================================================================================

def check_dvr_status(row, col_map):
    if is_stopped(): return None
    """
    Check trạng thái đầu ghi cho loop monitor.
    Trả về dict lỗi nếu lỗi, None nếu OK.
    """
    try:
        ip = str(row[col_map['ip']]).strip()
        code = str(row[col_map['code']]).strip()
        name = str(row[col_map['name']]).strip()
        
        if not ip or ip.lower() in ['nan', '']: return None
        
        # 1. Port Open -> OK (With 1 Retry)
        is_port_open = False
        for _ in range(2):
            if any(check_port(ip, p) for p in SCAN_PORTS):
                is_port_open = True
                break
            if _: time.sleep(0.5)
            
        if is_port_open:
            return {
                "Mã shop": code,
                "Tên shop": name,
                "IP": ip,
                "Kết quả": "Online",
                "Thời gian": datetime.now().strftime("%H:%M")
            }
        
        # 2. Port Closed -> Check Ping
        if ping_ip(ip):
             # Ping OK -> Error DVR
             return {
                 "Mã shop": code, 
                 "Tên shop": name, 
                 "IP": ip, 
                 "Kết quả": "Lỗi Đầu Ghi", 
                 "Thời gian": datetime.now().strftime("%H:%M")
             }
        
        return {
            "Mã shop": code,
            "Tên shop": name,
            "IP": ip,
            "Kết quả": "Offline",
            "Thời gian": datetime.now().strftime("%H:%M")
        }
        
    except: return None

