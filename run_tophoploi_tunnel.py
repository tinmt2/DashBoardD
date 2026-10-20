import os
import sys
import time
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

# 1. Don dep cloudflared cu neu co
try:
    subprocess.run(["taskkill", "/f", "/im", "cloudflared.exe"], capture_output=True)
except Exception:
    pass

# 2. Don dep cong 8000 neu bi chiem dung
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
print("     DASBOARDD - TEN MIEN CO DINH CHINH THUC: TOPHOPLOI.SITE")
print("==================================================================")
print(" [1] Ten mien chinh:   https://tophoploi.site")
print(" [2] Mang noi bo LAN:  http://10.96.25.111:8000")
print(" [3] Trang Quan Tri:   https://tophoploi.site/#/admin")
print("==================================================================")
print(" (Chi can giu 1 cua so CMD nay de ca he thong hoat dong lien tuc)")
print("==================================================================")
print("\n[+] Dang khoi dong Backend Server (Auto-Reload Enabled)...")

backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
backend_proc = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR)

time.sleep(2.5)
print("[v] Backend Server da san sang tren cong 8000!")
print("[+] Dang ket noi Cloudflare Tunnel vao ten mien tophoploi.site...\n")
time.sleep(1)

TOKEN = "eyJhIjoiYmQ2NzY1OTY2NDA1M2QwOGQxMWZkZjJiYjY0OGZmNTciLCJ0IjoiOTNkMWE0NzMtMzQwZC00OTU3LTk4YzgtZDI3MjMwZWJmNDhmIiwicyI6Ik16UTJOMlJrTW1VdE1Ua3laQzAwTURVNUxXRTVaakV0WWpWaVkyRTNNamMxWW1NdyJ9"
cloudflared_exe = os.path.join(ROOT_DIR, "cloudflared.exe")

try:
    subprocess.run([cloudflared_exe, "tunnel", "run", "--token", TOKEN])
except KeyboardInterrupt:
    print("\n[!] Da nhan Ctrl+C. Dang dong he thong...")
finally:
    try:
        backend_proc.terminate()
    except Exception:
        pass
    sys.exit(0)
