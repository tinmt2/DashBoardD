import os
import time
import threading
import socket
import struct
import pandas as pd
import hashlib
import json as _json
import requests
import concurrent.futures
import xml.etree.ElementTree as ET
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from app.services import backend_check, browser_manager
from app.services.ftel_playback_service import FtelPlaybackScanner

PASSWORDS = [
    "Dvkt#17010#@!",
    "Dvkt#17012#@!",
    "Dvkt#17011#@!",
    "fptadmin",
    "Admin12345"
]

BROWSER_SEMAPHORE = threading.Semaphore(4)
PLAYBACK_SEMAPHORE = threading.Semaphore(2)


# ─── Xiongmai DVRIP/Sofia binary protocol (port 34567) ───────────────────────

def _xm_sofia_hash(password: str) -> str:
    """Compute Xiongmai Sofia MD5 password hash (used by DVRIP protocol)."""
    if not password:
        return "tlJwpbo6"
    raw = hashlib.md5(password.encode()).digest()
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return "".join(chars[(raw[i] + raw[i + 1]) % len(chars)] for i in range(0, 16, 2))


def _xm_send(sock, session_id: int, seq: int, cmd: int, body: dict) -> None:
    """Send a Xiongmai binary protocol packet."""
    data = (_json.dumps(body, separators=(",", ":")) + "\n").encode()
    hdr = struct.pack("<BBBBIIBBHI",
        0xff, 0x00, 0x00, 0x00,
        session_id, seq,
        0, 0,
        cmd,
        len(data))
    sock.sendall(hdr + data)


def _xm_recv(sock, timeout: float = 6.0) -> dict:
    """Receive and parse a Xiongmai binary protocol response."""
    sock.settimeout(timeout)
    hdr = b""
    while len(hdr) < 20:
        chunk = sock.recv(20 - len(hdr))
        if not chunk:
            return {}
        hdr += chunk
    _, _, _, _, sid, _, _, _, cmd, dlen = struct.unpack("<BBBBIIBBHI", hdr)
    body = b""
    while len(body) < dlen:
        chunk = sock.recv(min(4096, dlen - len(body)))
        if not chunk:
            break
        body += chunk
    try:
        result = _json.loads(body.decode("utf-8", "replace").strip("\x00\n"))
        result["_sid"] = sid
        result["_cmd"] = cmd
        return result
    except Exception:
        return {"_sid": sid, "_cmd": cmd}


def xm_auth_34567(ip: str, password: str, username: str = "admin", timeout: float = 6.0) -> dict:
    """
    Authenticate to Xiongmai DVR via port 34567 (DVRIP/Sofia binary protocol).
    Returns: {success, ret, session_id, error}
    Ret codes: 100=OK, 101=WrongPass, 203=Locked, negative=connection error
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, 34567))
        _xm_send(sock, 0, 0, 1000, {
            "EncryptType": "MD5",
            "LoginType": "DVRIP",
            "PassWord": _xm_sofia_hash(password),
            "UserName": username,
        })
        resp = _xm_recv(sock, timeout)
        sock.close()
        if not resp:
            return {"success": False, "ret": -1, "session_id": 0, "error": "empty_response"}
        ret = resp.get("Ret", -99)
        sid_raw = resp.get("SessionID", "0x0")
        if isinstance(sid_raw, str) and sid_raw.startswith("0x"):
            sid = int(sid_raw, 16)
        elif isinstance(sid_raw, (int, float)):
            sid = int(sid_raw)
        else:
            sid = 0
        return {
            "success": ret == 100,
            "ret": ret,
            "session_id": sid,
            "error": None if ret == 100 else f"dvr_ret_{ret}",
        }
    except socket.timeout:
        return {"success": False, "ret": -3, "session_id": 0, "error": "timeout_34567"}
    except ConnectionRefusedError:
        return {"success": False, "ret": -4, "session_id": 0, "error": "refused_34567"}
    except OSError as e:
        return {"success": False, "ret": -5, "session_id": 0, "error": f"oserr:{e}"}
    except Exception as e:
        return {"success": False, "ret": -99, "session_id": 0, "error": f"exc:{e}"}


def xm_config_get(ip: str, session_id: int, name: str, timeout: float = 5.0):
    """
    Query a config/state from Xiongmai DVR via port 34567.
    Returns inner value (list/dict) or None on error.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, 34567))
        _xm_send(sock, session_id, 1, 1042, {
            "Name": name,
            "SessionID": "0x%08X" % session_id,
        })
        resp = _xm_recv(sock, timeout)
        sock.close()
        if resp.get("Ret") == 100:
            return resp.get(name) or resp
        return None
    except Exception:
        return None

class FtelDvrScanner:
                
    def __init__(self, df_data):
        self.df_data = df_data
        self.is_running = True
        self.on_log = None
        self.on_progress = None
        self.on_row_checked = None
        self.on_finished = None
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        if self.on_log: self.on_log("🚀 Bắt đầu quét kiểm tra đầu ghi Ftel...", "white")
        
        # Prepare rows list
        results = []
        for idx, row in self.df_data.iterrows():
            # Get existing password from Column H (index 7 or column names)
            existing_pwd = ""
            if len(row) > 7:
                existing_pwd = str(row.iloc[7]).strip()
            elif "Ticket add cam counting" in row:
                existing_pwd = str(row["Ticket add cam counting"]).strip()
            elif "Mật khẩu" in row:
                existing_pwd = str(row["Mật khẩu"]).strip()

            if existing_pwd.lower() in ["nan", "none", "sai pass", "-", ""]:
                existing_pwd = ""

            results.append({
                "index": idx,
                "ma_shop": str(row.get("Mã shop", "")).strip().removesuffix(".0"),
                "ten_shop": str(row.get("Tên shop", "")).strip(),
                "vung": str(row.get("Vùng", "")).strip(),
                "ip": str(row.get("IP", "")).strip(),
                "existing_password": existing_pwd,
                "status": "Chưa check",
                "cam_status": "-",
                "cam_online": 0,
                "cam_total": 0,
                "latency": "",
                "password": existing_pwd
            })

        total = len(results)
        completed = 0

        import concurrent.futures
        
        def _check_single_dvr_internal(item):
            if not self.is_running:
                return item
                
            import time
            ip = item["ip"]
            item["_t_start"] = time.time()
            item["_t_net_end"] = 0
            item["_t_login_start"] = 0
            item["_t_login_end"] = 0
            item["_t_cam_start"] = 0
            item["_t_cam_end"] = 0
            item["_t_play_start"] = 0
            item["_t_play_end"] = 0
            # Auth counters - must exist at function scope before any branch
            auth_rejected_count = 0
            technical_errors = 0
            
            from app.services.logging_utils import get_logger, job_id_var
            logger = get_logger("ftel_dvr")
            
            import time
            t_start = time.time()
            print(f"[FTEL-SCAN] START CHECK: [{item['index']+1}/{total}] Shop {item['ma_shop']} - IP: {ip}", flush=True)
            logger.info(f"[DVR-FTEL][{item['index']+1:03d}/{total}] Shop {item['ma_shop']} | IP={ip}", extra={
                "event": "SHOP_START",
                "metadata": {
                    "job_id": job_id_var.get(),
                    "shop_index": item["index"],
                    "total": total,
                    "warehouse_id": item["ma_shop"],
                    "warehouse_name": item["ten_shop"],
                    "ip": ip
                }
            })
            
            if not ip:
                item["status"] = "Không có IP"
                logger.info(f"[DVR-FTEL][{item['index']+1:03d}/{total}] Shop {item['ma_shop']} | {item['status']} | duration={int((time.time() - t_start) * 1000)}ms", extra={
                    "event": "SHOP_RESULT",
                    "metadata": {
                        "job_id": job_id_var.get(),
                        "shop_index": item["index"],
                        "total": total,
                        "warehouse_id": item["ma_shop"],
                        "warehouse_name": item["ten_shop"],
                        "ip": ip,
                        "status": item["status"],
                        "duration_ms": int((time.time() - t_start) * 1000)
                    }
                })
                return item
            
            try:
                # 1. PING CHECK
                try:
                    from ping3 import ping as ping3_ping
                except ImportError:
                    ping3_ping = None
                
                t0 = time.time()
                is_online = False
                latency_str = ""
                
                if ping3_ping:
                    lat = ping3_ping(ip, timeout=3, unit='ms')
                    if lat is not None and lat is not False:
                        is_online = True
                        latency_str = f"{round(lat, 1)} ms"
                
                if not is_online:
                    res = backend_check.ping_ip(ip)
                    elapsed = (time.time() - t0) * 1000
                    if res:
                        is_online = True
                        latency_str = f"{round(elapsed, 1)} ms"
                
                if not is_online:
                    item["status"] = "Offline"
                    return item
                
                item["status"] = "Online"
                item["latency"] = latency_str
                
                # 2. PASSWORD CHECK (Try port 81, then 82)
                open_ports = []
                for port in [81]:
                    if backend_check.check_port(ip, port):
                        open_ports.append(port)
                
                if not open_ports:
                    item["status"] = "Online (Đóng port)"
                    return item
                
                # Build list of passwords to try
                pwd_list = []
                if item["existing_password"]:
                    raw_pwd = str(item["existing_password"]).strip()
                    import re
                    # Sửa lỗi gõ Telex phổ biến: Dvvkt -> Dvkt
                    fixed_pwd = re.sub(r'([Dd])vv(kt)', r'\1v\2', raw_pwd, flags=re.IGNORECASE)
                    if fixed_pwd and fixed_pwd not in pwd_list:
                        pwd_list.append(fixed_pwd)
                    if raw_pwd and raw_pwd not in pwd_list:
                        pwd_list.append(raw_pwd)
                for p in PASSWORDS:
                    if p not in pwd_list:
                        pwd_list.append(p)
                
                verified_pwd = None
                verified_port = 81
                
                for port in open_ports:
                    # --- Platform detection (per port) ---
                    probe_url = f"http://{ip}:{port}/ISAPI/System/time"
                    is_hikvision = False
                    is_xiongmai = False
                    try:
                        probe = requests.get(probe_url, timeout=3)
                        if probe.status_code == 401:
                            is_hikvision = True
                            if self.on_log: self.on_log(f"   🔍 {item['ma_shop']} ({ip}:{port}): Phát hiện Hikvision ISAPI (401).", "gray")
                        elif probe.status_code == 200:
                            # Xiongmai trả về HTML 404 cho ISAPI URL
                            if "html" in probe.text.lower():
                                is_xiongmai = True
                                if self.on_log: self.on_log(f"   🔍 {item['ma_shop']} ({ip}:{port}): Phát hiện Xiongmai/OEM (HTML 200).", "gray")
                            else:
                                # Không cần auth, đã online
                                is_hikvision = True
                    except Exception as e:
                        if self.on_log: self.on_log(f"   [ERROR] {item['ma_shop']} ({ip}): Lỗi probe cổng {port}: {e}", "red")
                        continue

                    # --- Fetch XM random challenge once per port (before pwd loop) ---
                    import json as _json
                    xm_random = ""
                    if is_xiongmai:
                        try:
                            login_url_xm = f"http://{ip}:{port}/cgi-bin/login.cgi"
                            pre_resp = requests.post(
                                login_url_xm,
                                data=_json.dumps({"Name": "GetPreLoginInfo"}),
                                headers={"Content-Type": "text/plain"},
                                timeout=4
                            )
                            if pre_resp.status_code == 200:
                                pre_data = pre_resp.json()
                                xm_random = pre_data.get("Random", "")
                                if self.on_log: self.on_log(
                                    f"   🔐 {item['ma_shop']} ({ip}:{port}): XM Random={'có' if xm_random else 'không có (dùng MD5 thẳng)'}.",
                                    "gray"
                                )
                        except Exception:
                            xm_random = ""

                    def xm_hash(password, random):
                        """XM MD5: MD5(MD5(pwd).upper() + ':' + random) or MD5(pwd).upper() if no random"""
                        md5_pwd = hashlib.md5(password.encode()).hexdigest().upper()
                        if random:
                            return hashlib.md5((md5_pwd + ":" + random).encode()).hexdigest()
                        return md5_pwd

                    if is_hikvision:
                        pwd_idx = 0
                        for pwd in pwd_list:
                            pwd_idx += 1
                            t_pwd_start = time.time()
                            if not self.is_running:
                                break
                            try:
                                if pwd == item["existing_password"]:
                                    if self.on_log: self.on_log(f"   [AUTH] {item['ma_shop']} ({ip}): Ưu tiên thử pass sẵn có '{pwd}' cổng {port}...", "cyan")
                                else:
                                    if self.on_log: self.on_log(f"   ↳ {item['ma_shop']} ({ip}): Thử pass '{pwd}' trên cổng {port}...", "gray")
                                # --- Hikvision: Digest/Basic auth trên ISAPI ---
                                url = f"http://{ip}:{port}/ISAPI/System/time"
                                headers = {"X-Requested-With": "XMLHttpRequest"}
                                r = requests.get(url, auth=HTTPDigestAuth("admin", pwd), headers=headers, timeout=4)
                                if r.status_code == 401:
                                    r = requests.get(url, auth=HTTPBasicAuth("admin", pwd), headers=headers, timeout=4)
                                if r.status_code == 200:
                                    content_lower = r.text.lower()
                                    if "html" not in content_lower and "login" not in content_lower and "<?xml" in content_lower:
                                        verified_pwd = pwd
                                        verified_port = port
                                        item["_login_total_ms"] = item.get("_login_total_ms", 0) + int((time.time() - t_pwd_start)*1000)
                                        print(f"[FTEL-AUTH] IP={ip} ATTEMPT={pwd_idx} RESULT=SUCCESS DURATION={int((time.time() - t_pwd_start)*1000)/1000}s", flush=True)
                                        if self.on_log: self.on_log(f"   [AUTH] {item['ma_shop']} ({ip}): [SUCCESS] Hikvision khớp '{pwd}' cổng {port}!", "green")
                                        
                                        # --- Query Camera Status on Hikvision ---
                                        try:
                                            import xml.etree.ElementTree as ET
                                            cam_dict = {}
                                            
                                            # 1. Analog cameras
                                            sys_url = f"http://{ip}:{port}/ISAPI/System/Video/inputs/channels"
                                            rsys = requests.get(sys_url, auth=HTTPDigestAuth("admin", pwd), headers=headers, timeout=4)
                                            if rsys.status_code == 401:
                                                rsys = requests.get(sys_url, auth=HTTPBasicAuth("admin", pwd), headers=headers, timeout=4)
                                            if rsys.status_code == 200 and "<?xml" in rsys.text:
                                                try:
                                                    sroot = ET.fromstring(rsys.text)
                                                    for ch in sroot.findall(".//{*}VideoInputChannel"):
                                                        ch_id_el = ch.find(".//{*}id")
                                                        if ch_id_el is not None:
                                                            cam_dict[int(ch_id_el.text)] = "Online" # Analog defaults to Online
                                                except Exception: pass
                                            
                                            # 2. IP Cameras
                                            cam_url = f"http://{ip}:{port}/ISAPI/ContentMgmt/InputProxy/channels/status"
                                            rcam = requests.get(cam_url, auth=HTTPDigestAuth("admin", pwd), headers=headers, timeout=5)
                                            if rcam.status_code == 401:
                                                rcam = requests.get(cam_url, auth=HTTPBasicAuth("admin", pwd), headers=headers, timeout=5)
                                            if rcam.status_code == 200 and "<?xml" in rcam.text:
                                                try:
                                                    root = ET.fromstring(rcam.text)
                                                    for ch in root.findall(".//{*}InputProxyChannelStatus"):
                                                        ch_id_el = ch.find(".//{*}id")
                                                        if ch_id_el is not None:
                                                            online_el = ch.find(".//{*}online")
                                                            is_on = (online_el is not None and online_el.text.strip().lower() == "true")
                                                            cam_dict[int(ch_id_el.text)] = "Online" if is_on else "Offline"
                                                except Exception: pass

                                            total_c = len(cam_dict)
                                            online_c = 0
                                            details = []
                                            offline_channels = []
                                            
                                            for cid in sorted(cam_dict.keys()):
                                                ch_tag = f"CH{cid:02d}"
                                                if cam_dict[cid] == "Online":
                                                    online_c += 1
                                                    details.append(f"{ch_tag}: Online")
                                                else:
                                                    offline_channels.append(ch_tag)
                                                    details.append(f"{ch_tag}: Offline")
                                            
                                            if total_c > 0:
                                                item["cam_online"] = online_c
                                                print(f"[FTEL-CAMERA] RESULT ip={ip} online={online_c} total={total_c}", flush=True)
                                                item["cam_total"] = total_c
                                                item["cam_offline_list"] = offline_channels
                                                if len(offline_channels) == 0:
                                                    item["cam_status"] = f"{online_c} Cam"
                                                else:
                                                    item["cam_status"] = f"{online_c}/{total_c} Cam (Mất {', '.join(offline_channels)})"
                                                item["cam_details"] = "\n".join(details)
                                                if self.on_log: self.on_log(f"   📹 {item['ma_shop']} ({ip}): {item['cam_status']} ({', '.join(details[:8])}{'...' if len(details) > 8 else ''})", "cyan")
                                        except Exception as e_hcam:
                                            pass
                                            
                                        break
                                    else:
                                        if self.on_log: self.on_log(f"   [WARN] {item['ma_shop']} ({ip}): Hikvision trả HTML login — sai pass '{pwd}'.", "yellow")
                                else:
                                    item["_login_total_ms"] = item.get("_login_total_ms", 0) + int((time.time() - t_pwd_start)*1000)
                                    print(f"[FTEL-AUTH] IP={ip} ATTEMPT={pwd_idx} RESULT=INVALID DURATION={int((time.time() - t_pwd_start)*1000)/1000}s", flush=True)
                                    if self.on_log: self.on_log(f"   [FAIL] {item['ma_shop']} ({ip}): Hikvision HTTP {r.status_code} với pass '{pwd}'.", "red")
                            except Exception as e:
                                if self.on_log: self.on_log(f"   [ERROR] {item['ma_shop']} ({ip}): Lỗi kết nối cổng {port}: {e}", "red")

                    elif is_xiongmai:
                        item["_t_net_end"] = time.time()
                        try:
                            from selenium import webdriver
                            from selenium.webdriver.chrome.service import Service as ChromeService
                            from app.services import browser_manager
                            from selenium.webdriver.common.by import By
                            from selenium.webdriver.support.ui import WebDriverWait
                            from selenium.webdriver.support import expected_conditions as EC
                            from selenium.common.exceptions import NoAlertPresentException, TimeoutException
                            import tempfile
                            import os
                            
                            with BROWSER_SEMAPHORE:
                                item["_t_login_start"] = time.time()
                                if self.on_log: self.on_log(f"   🌐 {item['ma_shop']} ({ip}): Mở trình duyệt ẩn thử pass cổng {port}...", "gray")
                                print(f"[DEBUG-XM] [{ip}:{port}] Bat dau khoi tao Chrome headless...", flush=True)
                                driver = None
                                temp_dir = tempfile.mkdtemp()
                                try:
                                    options = webdriver.ChromeOptions()
                                    options.add_argument("--headless=new")
                                    options.add_argument("--disable-web-security")
                                    options.add_argument("--allow-running-insecure-content")
                                    options.add_argument("--disable-features=IsolateOrigins,site-per-process,BlockInsecurePrivateNetworkRequests")
                                    options.add_argument("--incognito")
                                    options.add_argument("--disable-features=LocalNetworkAccessChecks")
                                    options.add_argument(f"--user-data-dir={temp_dir}")
                                    options.add_argument("--window-size=1280,720")
                                    options.add_argument("--no-sandbox")
                                    options.add_argument("--disable-dev-shm-usage")
                                    options.add_argument("--ignore-certificate-errors")
                                    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                                    options.set_capability("unhandledPromptBehavior", "accept")
                                    
                                    print(f"[FTEL-WEB] LOCAL_NETWORK_ACCESS_CHECKS=DISABLED", flush=True)
                                    driver_path = browser_manager.get_bundled_driver_path()
                                    driver = webdriver.Chrome(service=ChromeService(executable_path=driver_path), options=options)
                                    print(f"[FTEL-WEB] CHROME_STARTED", flush=True)
                                    
                                    try:
                                        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                                            "source": '''
                                                window._xm_pushed_chn_status = null;
                                                if (window.console && window.console.log) { window._xm_original_log = window.console.log; }
                                                window.console.log = function() { if (!window._xm_original_log) return;
                                                    for (var i = 0; i < arguments.length; i++) {
                                                        var arg = arguments[i];
                                                        if (typeof arg === 'string' && arg.indexOf('"ChnStatus"') !== -1) {
                                                            try {
                                                                var jsonStr = arg.substring(arg.indexOf('{'));
                                                                var obj = JSON.parse(jsonStr);
                                                                if (obj.ChnStatus) window._xm_pushed_chn_status = obj.ChnStatus;
                                                            } catch(e) {}
                                                        }
                                                    }
                                                    window._xm_original_log.apply(window.console, arguments);
                                                };
                                                window.CheckPluginVersionExist = function(port, cb) { if (cb) cb({ Ret: 100, Version: "2.0.0.0" }); };
                                                window.checkPluginExist = function(cb) { if (cb) cb(54455); };
                                                window.detectPort = function(s, e, cb) { if (cb) cb(54455); };
                                                window.GetPluginVersion = function(cb) { if (cb) cb({ Ret: 100, Version: "2.0.0.0" }); };
                                            '''
                                        })
                                    except Exception as e:
                                        print(f"[DEBUG-XM] [{ip}:{port}] Loi inject CDP: {e}", flush=True)
                                        
                                    driver.set_page_load_timeout(15)
                                    try:
                                        print(f"[FTEL-WEB] NAVIGATE http://{ip}:{port}", flush=True)
                                        driver.get(f"http://{ip}:{port}")
                                        print(f"[FTEL-WEB] PAGE_LOADED", flush=True)
                                    except Exception as e:
                                        print(f"[DEBUG-XM] [{ip}:{port}] Loi driver.get(): {e}", flush=True)
                                    
                                    time.sleep(1)
                                    
                                    def find_els(ctx):
                                        try:
                                            alert = ctx.switch_to.alert
                                            alert.accept()
                                        except Exception:
                                            pass
                                        u, p, b = None, None, None
                                        for sel in ["#userName", "#login_userName_input", "#username", "input[name='username']", "input[name='user']", "input[type='text']"]:
                                            try:
                                                els = ctx.find_elements(By.CSS_SELECTOR, sel)
                                                for el in els:
                                                    if el.is_displayed() and el.is_enabled():
                                                        u = el; break
                                                if u: break
                                            except Exception: pass
                                        for sel in ["#loginPsw", "#login_user_input", "#password", "#login_password", "input[name='password']", "input[name='pwd']", "input[type='password']"]:
                                            try:
                                                els = ctx.find_elements(By.CSS_SELECTOR, sel)
                                                for el in els:
                                                    if el != u and el.is_displayed() and el.is_enabled():
                                                        p = el; break
                                                if p: break
                                            except Exception: pass
                                        for sel in ["#loginBtn", ".loginBtnNormal", "#login_btn_user_ok", "button[type='submit']", ".btn-login", "#btnLogin", "button", "input[type='button']"]:
                                            try:
                                                els = ctx.find_elements(By.CSS_SELECTOR, sel)
                                                for el in els:
                                                    if el.is_displayed() and el.is_enabled():
                                                        b = el; break
                                                if b: break
                                            except Exception: pass
                                        if not b:
                                            try:
                                                els = ctx.find_elements(By.CSS_SELECTOR, "div[class*='loginBtn'], div[id*='login_btn'], div[id*='loginBtn'], div[id*='LoginBtn'], div[id*='login']")
                                                for el in els:
                                                    if el.is_displayed() and el.is_enabled():
                                                        b = el; break
                                            except Exception: pass
                                        return u, p, b

                                    user_el, pass_el, btn_el = None, None, None
                                    print(f"[DEBUG-XM] [{ip}:{port}] Bat dau do form element (70 lan)...", flush=True)
                                    for _ in range(70):
                                        if not self.is_running:
                                            break
                                        user_el, pass_el, btn_el = find_els(driver)
                                        if user_el and pass_el and btn_el:
                                            print(f"[DEBUG-XM] [{ip}:{port}] Da tim thay form tai root document", flush=True)
                                            break
                                        time.sleep(0.5)

                                    if not (user_el and pass_el and btn_el):
                                        print(f"[DEBUG-XM] [{ip}:{port}] Khong thay o root, bat dau tim trong iframe...", flush=True)
                                        frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
                                        print(f"[DEBUG-XM] [{ip}:{port}] Co {len(frames)} iframe/frame tren trang.", flush=True)
                                        for i, frame in enumerate(frames):
                                            try:
                                                driver.switch_to.frame(frame)
                                                user_el, pass_el, btn_el = find_els(driver)
                                                if user_el and pass_el and btn_el:
                                                    print(f"[DEBUG-XM] [{ip}:{port}] Da tim thay form trong iframe so {i}", flush=True)
                                                    break
                                                driver.switch_to.default_content()
                                            except Exception:
                                                driver.switch_to.default_content()

                                    if not (user_el and pass_el and btn_el):
                                        print(f"[DEBUG-XM] [{ip}:{port}] Van khong thay form, thu refresh...", flush=True)
                                        try:
                                            time.sleep(1)
                                            driver.refresh()
                                            for _ in range(30):
                                                if not self.is_running:
                                                    break
                                                user_el, pass_el, btn_el = find_els(driver)
                                                if user_el and pass_el and btn_el:
                                                    print(f"[DEBUG-XM] [{ip}:{port}] Da tim thay form sau khi refresh", flush=True)
                                                    break
                                                time.sleep(0.5)
                                        except Exception as e:
                                            print(f"[DEBUG-XM] [{ip}:{port}] Loi khi refresh: {e}", flush=True)

                                    if not (user_el and pass_el and btn_el):
                                        if self.on_log: self.on_log(f"   🚨 {item['ma_shop']} ({ip}): Không tìm thấy form đăng nhập trên cổng {port}.", "red")
                                        print(f"[DEBUG-XM] [{ip}:{port}] THAT BAI TIM FORM! Dang chup anh...", flush=True)
                                        try:
                                            dbg_dir = os.path.join(tempfile.gettempdir(), "ftel_dvr_debug")
                                            os.makedirs(dbg_dir, exist_ok=True)
                                            dbg_path = os.path.join(dbg_dir, f"{ip.replace('.', '_')}_{port}.png")
                                            driver.save_screenshot(dbg_path)
                                            print(f"[DEBUG-XM] [{ip}:{port}] LUU ANH LOI TAI: {dbg_path}", flush=True)
                                            
                                            html_src = driver.page_source
                                            print(f"[DEBUG-XM] [{ip}:{port}] HTML Snippet (1000 chars): {html_src[:1000]}", flush=True)
                                        except Exception as dbg_e:
                                            print(f"[DEBUG-XM] [{ip}:{port}] Loi chup anh/lay HTML: {dbg_e}", flush=True)
                                            
                                        item["password"] = "Lỗi Form Web"
                                        continue
                                        
                                    print(f"[DEBUG-XM] [{ip}:{port}] Form san sang, bat dau thu pass...", flush=True)
                                    print(f"[FTEL-WEB] LOGIN_FORM_FOUND", flush=True)

                                    auth_rejected_count = 0
                                    technical_errors = 0
                                    for idx, pwd in enumerate(pwd_list):
                                        wrong_pass = False
                                        is_blocked = False
                                        is_success = False
                                        
                                        if not self.is_running:
                                            break
                                            
                                        if idx > 0:
                                            try:
                                                if not (user_el and pass_el and btn_el):
                                                    user_el, pass_el, btn_el = find_els(driver)
                                            except Exception:
                                                user_el, pass_el, btn_el = None, None, None
                                            
                                            if not (user_el and pass_el and btn_el):
                                                try:
                                                    driver.get(f"http://{ip}:{port}")
                                                    for _ in range(20):
                                                        user_el, pass_el, btn_el = find_els(driver)
                                                        if user_el and pass_el and btn_el:
                                                            break
                                                        time.sleep(0.5)
                                                except Exception:
                                                    pass

                                        if not (user_el and pass_el and btn_el):
                                            break

                                        if pwd == item["existing_password"]:
                                            if self.on_log: self.on_log(f"   🔑 {item['ma_shop']} ({ip}): Ưu tiên thử pass sẵn có '{pwd}' trên trình duyệt ẩn...", "cyan")
                                        else:
                                            if self.on_log: self.on_log(f"   ↳ {item['ma_shop']} ({ip}): Thử pass '{pwd}' trên trình duyệt ẩn...", "gray")

                                        if user_el and pass_el and btn_el:
                                            try:
                                                driver.execute_script('''
                                                    arguments[0].removeAttribute('readonly');
                                                    arguments[0].value = '';
                                                    arguments[0].value = arguments[1];
                                                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                                                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                                                    
                                                    arguments[2].removeAttribute('readonly');
                                                    arguments[2].value = '';
                                                    arguments[2].value = arguments[3];
                                                    arguments[2].dispatchEvent(new Event('input', { bubbles: true }));
                                                    arguments[2].dispatchEvent(new Event('change', { bubbles: true }));
                                                ''', user_el, "admin", pass_el, pwd)
                                            except Exception:
                                                try:
                                                    user_el.clear(); user_el.send_keys("admin")
                                                    pass_el.clear(); pass_el.send_keys(pwd)
                                                except: pass
                                                
                                            try:
                                                driver.execute_script("if (window.WebCms && window.WebCms.plugin) { window.WebCms.plugin.isLoaded = false; }")
                                            except Exception:
                                                pass

                                            try:
                                                driver.execute_script('''
                                                    var s = document.querySelectorAll('#LoginStatus, .LoginStatus, #Web_false');
                                                    s.forEach(function(el) { el.innerText = ''; el.textContent = ''; });
                                                ''')
                                            except Exception:
                                                pass

                                            time.sleep(0.3)
                                            try:
                                                driver.execute_script("arguments[0].click();", btn_el)
                                            except Exception:
                                                pass
                                            try:
                                                btn_el.click()
                                            except Exception:
                                                pass
                                            
                                            t_wait = time.time()
                                            while time.time() - t_wait < 9:
                                                time.sleep(0.5)
                                                
                                                try:
                                                    alert = driver.switch_to.alert
                                                    alert_text = alert.text.lower()
                                                    alert.accept()
                                                    auth_error_keywords = ["password", "pass", "lỗi mật khẩu", "sai mật khẩu", "invalid", "wrong", "not match", "incorrect", "login fail", "thất bại", "không đúng", "block", "lock", "exist"]
                                                    if any(k in alert_text for k in auth_error_keywords):
                                                        wrong_pass = True
                                                        if any(k in alert_text for k in ["block", "lock"]):
                                                            is_blocked = True
                                                            if self.on_log: self.on_log(f"   ⛔ {item['ma_shop']} ({ip}): Đầu ghi tạm khóa (alert: {alert_text[:50]}).", "yellow")
                                                        else:
                                                            if self.on_log: self.on_log(f"   ⚠ {item['ma_shop']} ({ip}): Sai pass '{pwd}' (alert: {alert_text[:50]}).", "yellow")
                                                        break
                                                except NoAlertPresentException:
                                                    pass
                                                except Exception:
                                                    pass
                                                
                                                for err_sel in ["#LoginStatus", ".LoginStatus", "#Web_false", "#ErrorTip", "#ErrTipRow"]:
                                                    try:
                                                        err_els = driver.find_elements(By.CSS_SELECTOR, err_sel)
                                                        for err_el in err_els:
                                                            if err_el.is_displayed() and err_el.text.strip():
                                                                err_msg = err_el.text.strip().lower()
                                                                if "bind browse" in err_msg or "plugin" in err_msg:
                                                                    continue
                                                                if any(w in err_msg for w in ["locked", "banned", "blocked"]):
                                                                    wrong_pass = True
                                                                    is_blocked = True
                                                                    if self.on_log: self.on_log(f"   ⛔ {item['ma_shop']} ({ip}): Đầu ghi tạm khóa do thử sai nhiều lần ({err_el.text.strip()[:60]}).", "yellow")
                                                                    break
                                                                if any(w in err_msg for w in ["username or password error", "password", "wrong", "invalid", "incorrect", "lỗi mật khẩu", "sai mật khẩu", "thất bại", "không đúng", "not exist", "exist"]):
                                                                    wrong_pass = True
                                                                    if self.on_log: self.on_log(f"   ⚠ {item['ma_shop']} ({ip}): Sai pass '{pwd}' ({err_el.text.strip()[:60]}).", "yellow")
                                                                    break
                                                        if wrong_pass:
                                                            break
                                                    except Exception:
                                                        pass
                                                if wrong_pass:
                                                    break
                                                
                                                try:
                                                    post_els = driver.find_elements(By.CSS_SELECTOR, "#logoutBtn, #LiveMenu, #playbackBtn, #Logout, .headerMenu, a[href*='logout']")
                                                    if any(el.is_displayed() for el in post_els):
                                                        is_success = True
                                                        break
                                                except Exception:
                                                    pass
                                                    
                                                try:
                                                    js_login = driver.execute_script('''
                                                        if (window.gDevice && (window.gDevice.bLogin === true || window.gDevice.bIsLogin === true)) return true;
                                                        if (window.g_bLogin === true || window.bLogin === true) return true;
                                                        if (window.WebCms && window.WebCms.isLogin === true) return true;
                                                        return false;
                                                    ''')
                                                    if js_login:
                                                        is_success = True
                                                        break
                                                except Exception:
                                                    pass
                                                    
                                                try:
                                                    curr_url = driver.current_url.lower()
                                                    if any(p in curr_url for p in ["live.html", "main.html", "playback.html", "preview.asp"]) and "login" not in curr_url:
                                                        is_success = True
                                                        break
                                                except Exception:
                                                    pass
                                                    
                                            if wrong_pass:
                                                auth_rejected_count += 1
                                            elif not is_success and not is_blocked:
                                                print(f"[FTEL-AUTH] TECHNICAL_TIMEOUT", flush=True)
                                                technical_errors += 1
                                                    
                                            if is_success:
                                                print(f"[FTEL-AUTH] LOGIN_SUCCESS", flush=True)
                                                print(f"[FTEL-WEB] GDEVICE_READY", flush=True)
                                                verified_pwd = pwd
                                                verified_port = port
                                                item["_t_login_end"] = time.time()
                                                if self.on_log: self.on_log(f"   🔑 {item['ma_shop']} ({ip}): ✅ Xiongmai khớp '{pwd}' cổng {port}!", "green")
                                                print(f"[DEBUG-XM] [{ip}:{port}] DANG NHAP THANH CONG VOI PASS '{pwd}'!", flush=True)
                                                
                                                try:
                                                    item["_t_cam_start"] = time.time()
                                                    xm_cam_data = driver.execute_async_script('''
                                                        var done = arguments[arguments.length - 1];
                                                        var out = { chnStatus: null, remoteV3: null, loginRsp: null };
                                                        
                                                        if (!window.gDevice || typeof window.gDevice.GetMsg !== 'function') {
                                                            return done(out);
                                                        }
                                                        
                                                        function queryMsg(name, cb, retries) {
                                                            if (retries === undefined) retries = 15;
                                                            if (window.gNet && window.gNet.run && retries > 0) {
                                                                setTimeout(function() { queryMsg(name, cb, retries - 1); }, 300);
                                                                return;
                                                            }
                                                            try {
                                                                window.gDevice.GetMsg(3, name, function(resp) {
                                                                    if (resp && resp.Ret === -10012 && retries > 0) {
                                                                        setTimeout(function() { queryMsg(name, cb, retries - 1); }, 500);
                                                                    } else {
                                                                        cb(resp);
                                                                    }
                                                                });
                                                            } catch(e) {
                                                                cb(null);
                                                            }
                                                        }
                                                        
                                                        queryMsg('NetWork.ChnStatus', function(resp) {
                                                            out.chnStatus = resp;
                                                            queryMsg('NetWork.RemoteDeviceV3', function(respV3) {
                                                                out.remoteV3 = respV3;
                                                                if (window.gDevice && window.gDevice.loginRsp) {
                                                                    out.loginRsp = window.gDevice.loginRsp;
                                                                }
                                                                done(out);
                                                            });
                                                        });
                                                        
                                                        setTimeout(function() { done(out); }, 8000);
                                                    ''')
                                                    
                                                    if xm_cam_data and isinstance(xm_cam_data, dict):
                                                        chn_status = xm_cam_data.get('chnStatus', {}).get('NetWork.ChnStatus', [])
                                                        remote_v3 = xm_cam_data.get('remoteV3', {}).get('NetWork.RemoteDeviceV3', [])
                                                        
                                                        connected_subnets = set()
                                                        for idx, c in enumerate(chn_status):
                                                            status = c.get('Status', '').strip().lower()
                                                            if status == 'connected':
                                                                ip_cam = ""
                                                                if idx < len(remote_v3):
                                                                    dec_list = remote_v3[idx].get('Decoder')
                                                                    dec = dec_list[0] if dec_list and isinstance(dec_list, list) and len(dec_list) > 0 else {}
                                                                    ip_cam = dec.get('IPAddress', '').strip()
                                                                if ip_cam and ip_cam != '0.0.0.0':
                                                                    parts = ip_cam.split('.')
                                                                    if len(parts) == 4:
                                                                        connected_subnets.add(f"{parts[0]}.{parts[1]}.{parts[2]}")
                                                        
                                                        actual_cams = []

                                                        
                                                        offline_cams = []

                                                        
                                                        details = []

                                                        
                                                        cam_list = []

                                                        
                                                        

                                                        
                                                        try:

                                                        
                                                            pushed_chn_status = driver.execute_async_script("""

                                                        
                                                                var cb = arguments[arguments.length - 1];

                                                        
                                                                if (window._xm_pushed_chn_status) { return cb(window._xm_pushed_chn_status); }

                                                        
                                                                var t = 0;

                                                        
                                                                var ival = setInterval(function() {

                                                        
                                                                    t += 200;

                                                        
                                                                    if (window._xm_pushed_chn_status || t >= 3000) {

                                                        
                                                                        clearInterval(ival);

                                                        
                                                                        cb(window._xm_pushed_chn_status || []);

                                                        
                                                                    }

                                                        
                                                                }, 200);

                                                        
                                                            """) or []

                                                        
                                                            pushed_map = {c.get('Chn', -1): c for c in pushed_chn_status if isinstance(c, dict)}

                                                        
                                                        except Exception:

                                                            pushed_map = {}


                                                        zero_mac_ips = {}
                                                        for temp_idx, temp_c in enumerate(chn_status):
                                                            temp_name = temp_c.get('ChnName', '').strip()
                                                            temp_status = temp_c.get('Status', '').strip().lower()
                                                            if not temp_name or temp_status == 'noconfig': continue
                                                            if temp_idx < len(remote_v3) and not remote_v3[temp_idx].get('Enable', True): continue
                                                            if temp_idx < len(remote_v3):
                                                                temp_dec_list = remote_v3[temp_idx].get('Decoder')
                                                                temp_dec = temp_dec_list[0] if temp_dec_list and isinstance(temp_dec_list, list) and len(temp_dec_list) > 0 else {}
                                                                t_mac = temp_dec.get('MacAddress', '').strip()
                                                                t_ip = temp_dec.get('IPAddress', '').strip()
                                                                if t_mac == '00:00:00:00:00:00' and t_ip and t_ip != '0.0.0.0':
                                                                    zero_mac_ips[t_ip] = zero_mac_ips.get(t_ip, 0) + 1

                                                        plugin_push_working = len(pushed_map) > 0
                                                        
                                                        import re
                                                        
                                                        for idx, c in enumerate(chn_status):
                                                            name = c.get('ChnName', '').strip()
                                                            status = c.get('Status', '').strip().lower()
                                                            
                                                            ch_tag = f"CH{idx + 1:02d}"
                                                            ip_cam = ""
                                                            mac_cam = ""
                                                            if idx < len(remote_v3):
                                                                dec_list = remote_v3[idx].get('Decoder')
                                                                dec = dec_list[0] if dec_list and isinstance(dec_list, list) and len(dec_list) > 0 else {}
                                                                ip_cam = dec.get('IPAddress', '').strip()
                                                                mac_cam = dec.get('MacAddress', '').strip()
                                                                
                                                            is_connected = (status == 'connected')
                                                            
                                                            pushed_info = pushed_map.get(idx)
                                                            if pushed_info:
                                                                err = pushed_info.get('Error', 0)
                                                                ret = pushed_info.get('Ret', 100)
                                                                if err != 0 or ret != 100:
                                                                    is_connected = False
                                                            
                                                            has_ip_config = (ip_cam and ip_cam != '0.0.0.0') or (mac_cam and mac_cam != '00:00:00:00:00:00')
                                                            
                                                            is_configured = False
                                                            name_lower = name.lower().replace(" ", "")
                                                            
                                                            # Advanced Heuristic for Default Names
                                                            # Matches: cam1, camera01, channel1, ch01, ipc, ipc1, ipc01, local, digital, etc.
                                                            is_default_name = not name_lower or bool(re.fullmatch(r'(cam|camera|channel|ch|ipc|ipcamera|local|digital)\d*', name_lower))
                                                                
                                                            if is_connected:
                                                                is_configured = True
                                                            elif has_ip_config:
                                                                zero_mac_count = zero_mac_ips.get(ip_cam, 0)
                                                                if mac_cam and mac_cam != '00:00:00:00:00:00':
                                                                    is_configured = True
                                                                elif zero_mac_count > 1:
                                                                    is_configured = False
                                                                else:
                                                                    is_configured = True
                                                            else:
                                                                if status == 'noconfig':
                                                                    is_configured = False
                                                                elif is_default_name and idx >= 8:
                                                                    is_configured = False
                                                                else:
                                                                    is_configured = True
                                                                    
                                                            # DEBUG LOGGING TO UNDERSTAND GHOST CAMERAS
                                                            print(f"[DEBUG-HEURISTIC] {ip} | IDX: {idx} | CH: {ch_tag} | NAME: '{name}' | LOWER: '{name_lower}' | DEFAULT: {is_default_name} | STATUS: '{status}' | IP_CFG: {has_ip_config} | IS_CONF: {is_configured}")
                                                                        
                                                            if is_configured:
                                                                actual_cams.append(ch_tag)
                                                                cam_obj = {"channel": ch_tag, "status": "Online" if is_connected else "Offline", "idx": idx, "offline_date": "-"}
                                                                if is_connected:
                                                                    details.append(f"{ch_tag}: Online")
                                                                else:
                                                                    offline_cams.append(ch_tag)
                                                                    details.append(f"{ch_tag}: Offline")
                                                                cam_list.append(cam_obj)
                                                                    
                                                        total_c = len(actual_cams)
                                                        online_c = total_c - len(offline_cams)
                                                        
                                                        if total_c == 0:
                                                            pushed_chn = driver.execute_script("return window._xm_pushed_chn_status;")
                                                            if pushed_chn and isinstance(pushed_chn, list):
                                                                for idx, c in enumerate(pushed_chn):
                                                                    ch_tag = f"CH{idx + 1:02d}"
                                                                    err = c.get("Error", 0)
                                                                    ret = c.get("Ret", 100)
                                                                    is_connected = (err == 0 and ret == 100)
                                                                    cam_status = "Online" if is_connected else "Offline"
                                                                    
                                                                    actual_cams.append(ch_tag)
                                                                    cam_list.append({"channel": ch_tag, "status": cam_status, "idx": idx, "offline_date": "-"})
                                                                    if is_connected:
                                                                        details.append(f"{ch_tag}: Online")
                                                                    else:
                                                                        offline_cams.append(ch_tag)
                                                                        details.append(f"{ch_tag}: Offline")
                                                                        
                                                                total_c = len(actual_cams)
                                                                online_c = total_c - len(offline_cams)
                                                            else:
                                                                dom_rows = driver.find_elements(By.CSS_SELECTOR, ".channelRow, [id^='channelRow_']")
                                                                if dom_rows:
                                                                    total_c = len(dom_rows)
                                                                    online_c = total_c
                                                                    details = [f"CH{i+1:02d}: Online" for i in range(total_c)]
                                                                    cam_list = [{"channel": f"CH{i+1:02d}", "status": "Online", "idx": i, "offline_date": "-"} for i in range(total_c)]
                                                                
                                                        if total_c > 0:
                                                            item["cam_online"] = online_c
                                                            item["cam_total"] = total_c
                                                            item["cam_offline_list"] = offline_cams
                                                            if len(offline_cams) == 0:
                                                                item["cam_status"] = f"{online_c} Cam"
                                                            else:
                                                                item["cam_status"] = f"{online_c}/{total_c} Cam (Mất {', '.join(offline_cams)})"
                                                            item["cam_details"] = "\n".join(details)
                                                            if self.on_log: self.on_log(f"   📹 {item['ma_shop']} ({ip}): {item['cam_status']} ({', '.join(details[:8])}{'...' if len(details) > 8 else ''})", "cyan")
                                                            
                                                            # Query Playback for Offline Cams
                                                            from datetime import datetime
                                                            now = datetime.now()
                                                            item["_t_play_start"] = time.time()
                                                            
                                                            playback = FtelPlaybackScanner()
                                                            for cam in cam_list:
                                                                if cam["status"] == "Offline":
                                                                    try:
                                                                        with PLAYBACK_SEMAPHORE:
                                                                            cal = playback.get_recording_calendar(driver, cam['idx'], now.year, now.month)
                                                                            
                                                                        err = cal.get("error")
                                                                        days = cal.get("recording_days", [])
                                                                        
                                                                        check_year = now.year
                                                                        check_month = now.month
                                                                        
                                                                        if not err and not days:
                                                                            # Fallback to previous month if current month has no recordings
                                                                            prev_month = now.month - 1
                                                                            prev_year = now.year
                                                                            if prev_month == 0:
                                                                                prev_month = 12
                                                                                prev_year -= 1
                                                                                
                                                                            with PLAYBACK_SEMAPHORE:
                                                                                cal_prev = playback.get_recording_calendar(driver, cam['idx'], prev_year, prev_month)
                                                                            
                                                                            if not cal_prev.get("error") and cal_prev.get("recording_days"):
                                                                                cal = cal_prev
                                                                                err = None
                                                                                days = cal.get("recording_days", [])
                                                                                check_year = prev_year
                                                                                check_month = prev_month
                                                                                
                                                                        if err:
                                                                            cam["offline_date"] = f"Lỗi: {err}"
                                                                        elif days:
                                                                            last_rec = days[-1]
                                                                            try:
                                                                                from datetime import timedelta
                                                                                last_dt = datetime(check_year, check_month, last_rec)
                                                                                off_dt = last_dt + timedelta(days=1)
                                                                                
                                                                                if (now - off_dt).days > 30:
                                                                                    off_date = "MKN lâu ngày"
                                                                                else:
                                                                                    off_date = off_dt.strftime('%Y-%m-%d')
                                                                            except Exception:
                                                                                off_date = "Chưa xác định"
                                                                            cam["offline_date"] = off_date
                                                                        else:
                                                                            cam["offline_date"] = "MKN lâu ngày"
                                                                    except Exception as e_pb:
                                                                        cam["offline_date"] = "Không kiểm tra được"
                                                            
                                                            import json
                                                            item["_t_cam_end"] = time.time()
                                                            item["cam_details"] = json.dumps(cam_list)
                                                            
                                                except Exception as e_xmcam:
                                                    print(f"[DEBUG-XM] [{ip}:{port}] Loi get camera data: {e_xmcam}", flush=True)
                                                    pass
                                                    
                                                break
                                            elif is_blocked:
                                                print(f"[DEBUG-XM] [{ip}:{port}] Blocked.", flush=True)
                                                break
                                            elif not wrong_pass:
                                                print(f"[DEBUG-XM] [{ip}:{port}] Khong login duoc voi pass (timeout) {pwd} (timeout hoac loi la).", flush=True)
                                                if self.on_log: self.on_log(f"   ⚠ {item['ma_shop']} ({ip}): Không đăng nhập được với pass '{pwd}'.", "yellow")
                                finally:
                                    if driver:
                                        try:
                                            driver.quit()
                                        except:
                                            pass
                                    if 'temp_dir' in locals() and temp_dir:
                                        import shutil
                                        try:
                                            shutil.rmtree(temp_dir, ignore_errors=True)
                                        except:
                                            pass
                        except Exception as xe:
                            print(f"[DEBUG-XM] [{ip}:{port}] Loi ngoai le Headless: {repr(str(xe))}", flush=True)
                            if self.on_log: self.on_log(f"   🚨 {item['ma_shop']} ({ip}): Lỗi Xiongmai Headless login: {xe}", "red")
                    if verified_pwd:
                        break
                
                if verified_pwd:
                    item["password"] = verified_pwd
                elif item.get("password") not in ["Lỗi Form Web", "Đầu ghi bị khóa"]:
                    # Default assignment if password was not found
                    if item.get("password") == "Lỗi Form Web":
                        pass
                    elif 'is_xiongmai' in locals() and is_xiongmai:
                        # For Xiongmai, rely on technical_errors vs auth_rejected
                        if auth_rejected_count == len(pwd_list) and len(pwd_list) > 0:
                            item["password"] = "Sai Pass"
                        else:
                            if technical_errors > 0:
                                item["password"] = "Lỗi Kỹ Thuật (Timeout)"
                            else:
                                item["password"] = "Sai Pass"
                    else:
                        item["password"] = "Sai Pass"

                    
            except Exception as e:
                import traceback
                err_str = str(e)
                if self.on_log: self.on_log(f"[ERROR] Ngoại lệ: {err_str}\n{traceback.format_exc()}", "red")
                item["status"] = "Lỗi check"
                item["latency"] = err_str
                
                logger.error(f"[DVR-FTEL][{item['index']+1:03d}/{total}] Shop {item['ma_shop']} | ERROR={type(e).__name__} | duration={int((time.time() - t_start) * 1000)}ms", extra={
                    "event": "SHOP_ERROR",
                    "metadata": {
                        "job_id": job_id_var.get(),
                        "shop_index": item["index"],
                        "warehouse_id": item["ma_shop"],
                        "ip": ip,
                        "error_type": type(e).__name__,
                        "error_message": err_str,
                        "duration_ms": int((time.time() - t_start) * 1000)
                    }
                })
                
            # Log RESULT
            print(f"[FTEL-RESULT] RESULT: [{item['index']+1}/{total}] Shop {item['ma_shop']} - IP: {ip} - STATUS: {item['status']}".encode("ascii", "ignore").decode("ascii"), flush=True)
            logger.info(f"[DVR-FTEL][{item['index']+1:03d}/{total}] Shop {item['ma_shop']} | {item['status']} | duration={int((time.time() - t_start) * 1000)}ms", extra={
                "event": "SHOP_RESULT",
                "metadata": {
                    "job_id": job_id_var.get(),
                    "shop_index": item["index"],
                    "total": total,
                    "warehouse_id": item["ma_shop"],
                    "warehouse_name": item["ten_shop"],
                    "ip": ip,
                    "status": item["status"],
                    "duration_ms": int((time.time() - t_start) * 1000)
                }
            })
            return item

        if self.on_log: self.on_log(f"Quét song song với tối đa {backend_check.MAX_WORKERS} workers...", "white")
        
        
        def check_single_dvr(item):
            try:
                res = _check_single_dvr_internal(item)
            except Exception as e:
                import traceback
                print(f"[FTEL-DEBUG] Crash at {item.get('ip')}: {e}\n{traceback.format_exc()}", flush=True)
                item["status"] = "Lỗi hệ thống"
                res = item
            
            # Calculate times
            if res and "_t_start" in res:
                t_total_end = time.time()
                t_start = res["_t_start"]
                t_net_end = res["_t_net_end"] or t_total_end
                t_login_start = res["_t_login_start"] or t_net_end
                t_login_end = res["_t_login_end"] or t_login_start
                t_cam_start = res["_t_cam_start"] or t_login_end
                t_cam_end = res["_t_cam_end"] or t_cam_start
                t_play_start = res["_t_play_start"] or t_cam_end
                t_play_end = res["_t_play_end"] or t_play_start
                
                net_ms = int((t_net_end - t_start) * 1000)
                log_ms = res.get("_login_total_ms", 0)
                cam_ms = int((t_cam_end - t_cam_start) * 1000)
                play_ms = int((t_play_end - t_play_start) * 1000)
                total_ms = int((t_total_end - t_start) * 1000)
                
                print(f"[FTEL-PERF] IP={res.get('ip')} NETWORK={net_ms}ms LOGIN={log_ms}ms CAMERA={cam_ms}ms PLAYBACK={play_ms}ms TOTAL={total_ms}ms", flush=True)
            return res

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=backend_check.MAX_WORKERS)
        try:
            futures = {executor.submit(check_single_dvr, item): item for item in results}
            for f in concurrent.futures.as_completed(futures):
                if not self.is_running:
                    executor.shutdown(wait=False)
                    break
                
                completed += 1
                try:
                    item_res = f.result()
                except Exception as e:
                    import traceback
                    if self.on_log: self.on_log(f"[ERROR] Worker thread exception: {e}", "red")
                    item_res = futures.get(f)
                    if item_res:
                        item_res["status"] = "Lỗi exception"
                    else:
                        continue
                
                # Emit update for table row
                if self.on_row_checked: self.on_row_checked(
                    item_res["index"], 
                    item_res["status"], 
                    item_res.get("cam_status", "-"),
                    item_res.get("cam_details", ""),
                    item_res["latency"],
                    item_res["password"],
                    item_res.get("cam_online", 0),
                    item_res.get("cam_total", 0)
                )
                if self.on_progress: self.on_progress(completed, total)
                from app.services.logging_utils import get_logger
                get_logger("ftel_dvr").info(f"[DVR-FTEL][JOB_PROGRESS] {completed}/{total} | {completed*100/total:.2f}%", extra={
                    "event": "JOB_PROGRESS",
                    "metadata": {"completed": completed, "total": total, "shop_index": item_res["index"]}
                })
                
                if "Online" in item_res["status"]:
                    color = "green"
                else:
                    color = "red"
                cam_txt = f" | Cam: {item_res.get('cam_status', '-')}" if item_res.get("cam_status", "-") != "-" else ""
                if self.on_log: self.on_log(
                    f"[{completed}/{total}] Shop {item_res['ma_shop']} ({item_res['ip']}): {item_res['status']}{cam_txt} | Pass: {item_res['password']}",
                    color
                )
        finally:
            executor.shutdown(wait=False)
            
        if self.on_log: self.on_log("[SUCCESS] Hoàn thành quét tất cả đầu ghi Ftel!", "green")
        print(f"[FTEL-PERF] TOTAL JOB={total} DVRs", flush=True)
        print(f"[FTEL-PERF] NETWORK CONCURRENCY={backend_check.MAX_WORKERS}", flush=True)
        print(f"[FTEL-PERF] BROWSER CONCURRENCY=4", flush=True)
        print(f"[FTEL-PERF] PLAYBACK CONCURRENCY=2", flush=True)
        if self.on_finished: self.on_finished(results)




