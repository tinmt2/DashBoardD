import os
import sys
import time
import subprocess
import threading

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

# 1. Don dep cloudflared cu neu co
try:
    subprocess.run(["taskkill", "/f", "/im", "cloudflared.exe"], capture_output=True)
except Exception:
    pass

# 2. Don dep cong 8000 neu bi treo
try:
    import psutil
    current_pid = os.getpid()
    for conn in psutil.net_connections():
        if conn.laddr and conn.laddr.port == 8000 and conn.pid != current_pid:
            try:
                psutil.Process(conn.pid).terminate()
            except Exception:
                pass
except Exception:
    pass

time.sleep(1)

print("==================================================================")
print("   DASBOARDD + CLOUDFLARE TUNNEL (1 CUA SO CMD DUY NHAT)")
print("==================================================================")
print(" [1] Backend Port 8000: Khoi dong ngam ben trong cung CMD")
print(" [2] Mang noi bo LAN:   http://10.96.25.111:8000")
print(" [3] Trang Quan Tri:    http://10.96.25.111:8000/#/admin")
print("==================================================================")
print(" (Chi can giu 1 cua so CMD nay. Khi dong CMD la tat toan bo)")
print("==================================================================")
print("\n[+] Dang khoi dong Backend Server...")

import uvicorn
from app.main import app

def run_backend():
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config=config)
    server.run()

backend_thread = threading.Thread(target=run_backend, daemon=True)
backend_thread.start()

time.sleep(2)
print("[v] Backend Server da san sang tren cong 8000!")
print("[+] Dang ket noi Cloudflare Tunnel truc tiep ben duoi...\n")
time.sleep(1)

cloudflared_exe = os.path.join(ROOT_DIR, "cloudflared.exe")
try:
    subprocess.run([cloudflared_exe, "tunnel", "--url", "http://localhost:8000"])
except KeyboardInterrupt:
    print("\n[!] Da nhan Ctrl+C. Dang dong he thong...")
    sys.exit(0)
