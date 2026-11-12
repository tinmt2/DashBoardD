#!/usr/bin/env python3
"""
Launcher khởi chạy độc lập cho FastAPI Backend (Test-LC)
- Chạy độc lập, không phụ thuộc Electron
- Kiểm tra và xác minh an toàn đa tầng cho port 18020
- Chỉ bind vào loopback 127.0.0.1:18020
- Đặt working directory tại gốc repository
"""

import sys
import os
import time
import socket
import json
import urllib.request
import urllib.error
from pathlib import Path

# Đảm bảo Project Root luôn là thư mục làm việc và nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PORT = 18020
HOST = "127.0.0.1"


def is_port_in_use(host: str, port: int) -> bool:
    """Kiểm tra xem port có đang lắng nghe hay không."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def verify_occupant_is_test_lc(host: str, port: int) -> bool:
    """
    Bước A: Xác minh danh tính qua HTTP GET /health.
    Phải trả về status=ok và service=test-python-backend.
    """
    url = f"http://{host}:{port}/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Test-LC-Launcher"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                if body.get("status") == "ok" and body.get("service") == "test-python-backend":
                    return True
    except Exception:
        pass
    return False


def get_pids_listening_on_port(port: int) -> list[int]:
    """Tìm PID của tiến trình đang lắng nghe trên cổng chỉ định (Windows netstat)."""
    pids = []
    try:
        import subprocess
        out = subprocess.check_output(f'netstat -ano | findstr LISTENING | findstr :{port}', shell=True, text=True)
        for line in out.strip().splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and f":{port}" in parts[1]:
                try:
                    pid = int(parts[-1])
                    if pid > 0 and pid not in pids:
                        pids.append(pid)
                except ValueError:
                    pass
    except Exception:
        pass
    return pids


def verify_and_safely_free_port(host: str, port: int) -> bool:
    """
    Quy trình 4 bước kiểm tra và xử lý xung đột port an toàn:
    1. Kiểm tra port có đang mở kết nối không.
    2. Gửi request /health xác minh đúng là backend Test-LC cũ.
    3. Kiểm tra PID, executable, commandline / path của tiến trình.
    4. Chỉ dừng tiến trình khi có đầy đủ 100% bằng chứng là backend cũ.
    """
    if not is_port_in_use(host, port):
        return True

    print(f"[PORT CHECK] Cổng {port} đang có tiến trình chiếm dụng. Đang xác minh danh tính...")

    # Bước A: Kiểm tra danh tính qua health check
    if not verify_occupant_is_test_lc(host, port):
        print(f"[CẢNH BÁO AN TOÀN] Cổng {port} bị chiếm bởi một ứng dụng KHÔNG PHẢI Test-LC hoặc không phản hồi đúng chuẩn.")
        print("[HÀNH ĐỘNG] Dừng khởi động để tránh xung đột hoặc tắt nhầm ứng dụng khác của người dùng.")
        return False

    # Bước B: Tìm PID
    pids = get_pids_listening_on_port(port)
    current_pid = os.getpid()
    candidate_pids = [p for p in pids if p != current_pid]

    if not candidate_pids:
        print(f"[CẢNH BÁO AN TOÀN] Không tìm thấy PID của tiến trình chiếm cổng {port}. Dừng khởi động.")
        return False

    # Bước C: Xác minh PID qua psutil
    try:
        import psutil
    except ImportError:
        print("[CẢNH BÁO] Không có thư viện psutil để xác minh PID an toàn. Dừng khởi động.")
        return False

    verified_procs = []
    project_root_str = str(PROJECT_ROOT).lower()

    for pid in candidate_pids:
        try:
            p = psutil.Process(pid)
            p_name = p.name().lower()
            p_exe = (p.exe() or "").lower()
            p_cmdline = " ".join(p.cmdline() or []).lower()

            p_cwd = ""
            try:
                p_cwd = (p.cwd() or "").lower()
            except Exception:
                pass

            # Phải là python.exe hoặc backend.exe
            if not ("python" in p_name or "backend" in p_name):
                print(f"[TỪ CHỐI DIỆT] PID {pid} là '{p_name}', không phải python.exe.")
                return False

            # Tuyệt đối không được là Electron hoặc Node
            if "electron" in p_name or "node" in p_name or "electron" in p_cmdline:
                print(f"[TỪ CHỐI DIỆT] PID {pid} thuộc về Electron/Node.")
                return False

            # Đường dẫn phải liên quan đến project root hoặc virtualenv hiện tại
            is_our_project = (
                (project_root_str in p_cmdline)
                or (project_root_str in p_exe)
                or (".venv" in p_exe)
                or (project_root_str in p_cwd and "app.api.main" in p_cmdline)
            )
            if not is_our_project:
                print(f"[TỪ CHỐI DIỆT] PID {pid} chạy từ đường dẫn lạ: {p_exe} (Cwd: {p_cwd}). Không thuộc thư mục dự án {PROJECT_ROOT}.")
                return False

            verified_procs.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"[CẢNH BÁO] Không thể truy cập thông tin PID {pid}: {e}. Dừng khởi động.")
            return False

    if not verified_procs:
        print("[CẢNH BÁO] Không xác minh được tiến trình hợp lệ để giải phóng port. Dừng khởi động.")
        return False

    # Bước D: Dừng tiến trình mồ côi đã được xác minh 100%
    for p in verified_procs:
        print(f"[SAFE CLEANUP] Đã xác minh 100% PID {p.pid} ({p.name()}) là backend Test-LC mồ côi cũ. Đang giải phóng...")
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

    # Chờ port được giải phóng hoàn toàn (tối đa 5s)
    for _ in range(10):
        time.sleep(0.5)
        if not is_port_in_use(host, port):
            print(f"[SUCCESS] Cổng {port} đã được giải phóng an toàn.")
            return True

    print(f"[LỖI] Cổng {port} vẫn bận sau khi giải phóng. Dừng khởi động.")
    return False


def main():
    print("=" * 65)
    print("  TEST-LC BACKEND STANDALONE LAUNCHER (Phase 1)")
    print(f"  Working Directory: {PROJECT_ROOT}")
    print(f"  Target Binding:    http://{HOST}:{PORT}")
    print("=" * 65)

    # 1. Kiểm tra và giải phóng port an toàn
    if not verify_and_safely_free_port(HOST, PORT):
        print("\n[STOP] Khởi động bị hủy do an toàn cổng 18020. Vui lòng kiểm tra lại.")
        sys.exit(1)

    # 2. Khởi chạy Uvicorn độc lập
    print(f"\n[INFO] Khởi chạy FastAPI Uvicorn tại http://{HOST}:{PORT} ...\n")
    import uvicorn
    from app.api.main import app

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=False
    )


if __name__ == "__main__":
    main()
