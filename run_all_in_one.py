import os
import sys
import time
import subprocess
import threading

# 1. Thiet lap duong dan thu muc
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

# 2. Don dep tien trinh ngrok cu neu co de tranh trung lap domain
try:
    subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], capture_output=True)
except Exception:
    pass

# 3. Kiem tra va don dep cong 8000 neu tien trinh cu con sot lai
try:
    import psutil
    current_pid = os.getpid()
    for conn in psutil.net_connections():
        if conn.laddr and conn.laddr.port == 8000 and conn.pid != current_pid:
            try:
                p = psutil.Process(conn.pid)
                p.terminate()
            except Exception:
                pass
except Exception:
    pass

time.sleep(1)

# In thong tin he thong
print("==================================================================")
print("     DASBOARDD - KHOI DONG TOAN BO TRONG 1 CUA SO CMD DUY NHAT")
print("==================================================================")
print(" [1] Backend Server:   http://localhost:8000")
print(" [2] Mang noi bo LAN:  http://10.96.25.111:8000 (Dung cho 2 may trong phong)")
print(" [3] Ten mien NGROK:   https://zips-linoleum-anchovy.ngrok-free.dev")
print(" [4] Trang Quan tri:   http://10.96.25.111:8000/#/admin")
print("==================================================================")
print(" (Chi can giu 1 cua so CMD nay. Khi dong CMD la tat toan bo)")
print("==================================================================")
print("\n[+] Dang khoi dong Backend Server tren cong 8000...")

# 4. Khoi dong FastAPI Backend trong thread rieng
import uvicorn
from app.main import app

def run_backend():
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="warning"
    )
    server = uvicorn.Server(config=config)
    server.run()

backend_thread = threading.Thread(target=run_backend, daemon=True)
backend_thread.start()

# Cho backend khoi dong xong
time.sleep(2.5)
print("[v] Backend Server da san sang tren cong 8000!")
print("[+] Dang ket noi duong ham NGROK truc tiep ben duoi...\n")
time.sleep(1)

# 5. Khoi dong Ngrok truc tiep trong cua so CMD nay
ngrok_exe = os.path.join(ROOT_DIR, "ngrok.exe")
try:
    subprocess.run([ngrok_exe, "http", "--url=https://zips-linoleum-anchovy.ngrok-free.dev", "8000"])
except KeyboardInterrupt:
    print("\n[!] Da nhan Ctrl+C. Dang dong he thong...")
    sys.exit(0)
