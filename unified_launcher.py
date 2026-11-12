#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED LAUNCHER - DashBoardD & Test Application Engine
Phase 9.3 Consolidated Implementation (Adaptive Path Resolution)
Standard Library only: sys, os, subprocess, time, urllib, socket, shutil, signal, webbrowser
"""

import sys
import os
import time
import socket
import shutil
import signal
import urllib.request
import urllib.error
import json
import subprocess
import webbrowser

# ==============================================================================
# 1. DIRECTORY & PATH RESOLUTION (ADAPTIVE & CONSOLIDATED)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Adaptive resolution: handles running either inside DashBoardD root or from ABC parent directory
if os.path.exists(os.path.join(BASE_DIR, "test_engine")):
    DASHBOARD_DIR = BASE_DIR
    TEST_DIR = os.path.join(BASE_DIR, "test_engine")
elif os.path.exists(os.path.join(BASE_DIR, "DashBoardD", "test_engine")):
    DASHBOARD_DIR = os.path.join(BASE_DIR, "DashBoardD")
    TEST_DIR = os.path.join(BASE_DIR, "DashBoardD", "test_engine")
else:
    DASHBOARD_DIR = os.path.join(BASE_DIR, "DashBoardD")
    TEST_DIR = os.path.join(BASE_DIR, "test")

DASHBOARD_BACKEND_DIR = os.path.join(DASHBOARD_DIR, "backend")
DASHBOARD_FRONTEND_DIR = os.path.join(DASHBOARD_DIR, "dashboard-app")
DASHBOARD_DIST_INDEX = os.path.join(DASHBOARD_FRONTEND_DIR, "dist", "index.html")

PYTHON_EXE = sys.executable

# Track processes spawned EXCLUSIVELY by this launcher session
SPAWNED_PROCESSES = []  # List of tuples: (name, popen_obj)


# ==============================================================================
# 2. HEALTH & PORT INSPECTION (NON-DESTRUCTIVE)
# ==============================================================================
def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a TCP port is accepting connections without altering state."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        try:
            return s.connect_ex((host, port)) == 0
        except Exception:
            return False


def probe_health_endpoint(url: str, expected_snippet: str = None) -> bool:
    """Probes a health check endpoint via HTTP GET."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "UnifiedLauncher-HealthCheck/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8", errors="ignore")
                if expected_snippet:
                    return expected_snippet in body
                return True
    except Exception:
        pass
    return False


def inspect_service(name: str, port: int, health_url: str, expected_snippet: str):
    """
    Evaluates whether a service is:
    - 'FREE': Port is unoccupied.
    - 'RUNNING_VALID': Port is active and passes expected health check (safe to reuse).
    - 'CONFLICT_UNKNOWN': Port is occupied but fails health check (do NOT kill).
    """
    if not is_port_listening(port):
        return "FREE"
    
    if probe_health_endpoint(health_url, expected_snippet):
        return "RUNNING_VALID"
    
    return "CONFLICT_UNKNOWN"


def wait_for_service(name: str, health_url: str, expected_snippet: str, timeout: int = 15) -> bool:
    """Polls a health endpoint until it passes or timeout expires."""
    print(f"   [Chờ] Đang kiểm tra cổng sẵn sàng của {name} ({health_url})...", end="", flush=True)
    start_time = time.time()
    while time.time() - start_time < timeout:
        if probe_health_endpoint(health_url, expected_snippet):
            print(" [OK]")
            return True
        time.sleep(0.5)
        print(".", end="", flush=True)
    print(" [HẾT GIỜ]")
    return False


# ==============================================================================
# 3. SERVICE LAUNCHERS
# ==============================================================================
def start_dashboard_backend():
    """Starts or reuses DashBoardD FastAPI backend on port 8000."""
    status = inspect_service("DashBoardD Backend", 8000, "http://127.0.0.1:8000/api/health", "ok")
    if status == "RUNNING_VALID":
        print("   [+] DashBoardD Backend (Port 8000): Đã đang chạy và hoạt động tốt (Tái sử dụng an toàn).")
        return True
    elif status == "CONFLICT_UNKNOWN":
        print("   [!] CẢNH BÁO: Cổng 8000 đang bị chiếm dụng bởi tiến trình không phải DashBoardD!")
        print("       Launcher sẽ KHÔNG kill tiến trình lạ. Vui lòng kiểm tra và giải phóng cổng 8000.")
        return False
    
    # Port is free -> Spawn
    print("   [+] Đang khởi động DashBoardD Backend trên cổng 8000...")
    cmd = [PYTHON_EXE, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    proc = subprocess.Popen(
        cmd,
        cwd=DASHBOARD_BACKEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    SPAWNED_PROCESSES.append(("DashBoardD Backend (Port 8000)", proc))
    return wait_for_service("DashBoardD Backend", "http://127.0.0.1:8000/api/health", "ok", timeout=12)


def start_test_backend():
    """Starts or reuses Test Engine FastAPI backend on port 18020."""
    status = inspect_service("Test Engine Backend", 18020, "http://127.0.0.1:18020/health", "test-python-backend")
    if status == "RUNNING_VALID":
        print("   [+] Test Engine Backend (Port 18020): Đã đang chạy và hoạt động tốt (Tái sử dụng an toàn).")
        return True
    elif status == "CONFLICT_UNKNOWN":
        print("   [!] CẢNH BÁO: Cổng 18020 đang bị chiếm dụng bởi tiến trình không phải Test Engine!")
        print("       Launcher sẽ KHÔNG kill tiến trình lạ. Vui lòng kiểm tra và giải phóng cổng 18020.")
        return False
    
    # Port is free -> Spawn
    print(f"   [+] Đang khởi động Test Engine Backend trên cổng 18020 (CWD: {TEST_DIR})...")
    cmd = [PYTHON_EXE, "-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "18020", "--no-access-log"]
    proc = subprocess.Popen(
        cmd,
        cwd=TEST_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    SPAWNED_PROCESSES.append(("Test Engine Backend (Port 18020)", proc))
    return wait_for_service("Test Engine Backend", "http://127.0.0.1:18020/health", "test-python-backend", timeout=12)


def start_dev_frontend():
    """Starts or reuses Vite dev server on port 5174."""
    status = inspect_service("Frontend Dev Server", 5174, "http://localhost:5174", "<html")
    if status == "RUNNING_VALID":
        print("   [+] Frontend Dev Server (Port 5174): Đã đang chạy (Tái sử dụng).")
        return True
    elif status == "CONFLICT_UNKNOWN":
        print("   [!] CẢNH BÁO: Cổng 5174 đang bị chiếm bởi tiến trình không xác định!")
        return False
    
    npm_path = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm_path:
        print("   [!] LỖI: Không tìm thấy 'npm' trên hệ thống để khởi động Frontend Dev Server.")
        return False

    print("   [+] Đang khởi động Frontend Dev Server (Vite) trên cổng 5174...")
    cmd = f'"{npm_path}" run dev'
    proc = subprocess.Popen(
        cmd,
        cwd=DASHBOARD_FRONTEND_DIR,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    SPAWNED_PROCESSES.append(("Frontend Dev Server (Port 5174)", proc))
    return wait_for_service("Frontend Dev Server", "http://localhost:5174", None, timeout=12)


# ==============================================================================
# 4. CLEAN SHUTDOWN HANDLER (CONTROLLED & SAFE)
# ==============================================================================
def clean_shutdown():
    """Stops ONLY processes spawned by this launcher run."""
    if not SPAWNED_PROCESSES:
        print("\n>> Không có tiến trình con nào cần dừng (Tất cả dịch vụ là tiến trình độc lập có từ trước).")
        return

    print("\n" + "=" * 65)
    print(">> ĐANG DỪNG CÓ KIỂM SOÁT CÁC TIẾN TRÌNH CON ĐƯỢC TẠO TRONG PHIÊN NÀY:")
    print("=" * 65)
    
    for name, proc in SPAWNED_PROCESSES:
        if proc.poll() is None:
            print(f"   - [Dừng] {name} (PID: {proc.pid})...")
            try:
                # Windows taskkill tree for this specific spawned PID only
                subprocess.run(
                    f"taskkill /F /T /PID {proc.pid}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"     Lỗi khi dừng {name}: {e}")
        else:
            print(f"   - [Đã tắt] {name} (PID: {proc.pid})")
    
    print(">> Đã hoàn tất dọn dẹp các tiến trình con an toàn.")


# ==============================================================================
# 5. EXECUTION MODES
# ==============================================================================
def run_status_check():
    """Non-destructive status audit of all system ports and health endpoints."""
    print("\n" + "=" * 65)
    print("   KIỂM TRA TRẠNG THÁI HỆ THỐNG (READ-ONLY AUDIT)")
    print("=" * 65)
    print(f"   Base Dir:          {BASE_DIR}")
    print(f"   Dashboard Backend: {DASHBOARD_BACKEND_DIR}")
    print(f"   Test Engine:       {TEST_DIR}")
    print("-" * 65)
    
    services = [
        ("DashBoardD Backend", 8000, "http://127.0.0.1:8000/api/health", "ok"),
        ("Test Engine Backend", 18020, "http://127.0.0.1:18020/health", "test-python-backend"),
        ("Frontend Dev Server", 5174, "http://localhost:5174", None),
        ("Production Web Server", 8000, "http://localhost:8000/", "<html"),
    ]
    
    for name, port, url, snippet in services:
        status = inspect_service(name, port, url, snippet)
        if status == "RUNNING_VALID":
            print(f"   [ONLINE] {name:25} | Cổng: {port:5} | Health: SẴN SÀNG ({url})")
        elif status == "CONFLICT_UNKNOWN":
            print(f"   [CẢNH BÁO] {name:25} | Cổng: {port:5} | Xung đột: Cổng bị chiếm dụng bởi service lạ")
        else:
            print(f"   [OFFLINE] {name:25} | Cổng: {port:5} | Đang tắt")
            
    print("-" * 65)
    print(f"   Frontend Dist Build: {'ĐÃ BUILD (Sẵn sàng cho Production)' if os.path.exists(DASHBOARD_DIST_INDEX) else 'CHƯA BUILD (Cần npm run build)'}")
    print("=" * 65)


def run_dev_mode():
    """Executes Development Mode: Port 8000, Port 18020, Port 5174."""
    print("\n" + "=" * 65)
    print("   KHỞI CHẠY HỆ THỐNG - CHẾ ĐỘ PHÁT TRIỂN (DEV MODE)")
    print("=" * 65)
    print(">> Dịch vụ yêu cầu:")
    print("   1. DashBoardD Backend  : http://localhost:8000")
    print(f"   2. Test Engine Backend : http://localhost:18020 ({TEST_DIR})")
    print("   3. Frontend Dev Server : http://localhost:5174 (Hot Reload)")
    print("-" * 65)

    # 1. Start DashBoardD backend
    if not start_dashboard_backend():
        print("[!] Không thể khởi động DashBoardD Backend. Hủy quy trình.")
        clean_shutdown()
        return False

    # 2. Start Test backend
    if not start_test_backend():
        print("[!] Không thể khởi động Test Engine Backend. Hủy quy trình.")
        clean_shutdown()
        return False

    # 3. Start Frontend dev server
    if not start_dev_frontend():
        print("[!] Không thể khởi động Frontend Dev Server. Hủy quy trình.")
        clean_shutdown()
        return False

    dev_url = "http://localhost:5174"
    print("\n" + "=" * 65)
    print(">> TẤT CẢ DỊCH VỤ DEV ĐÃ SẴN SÀNG VÀ VƯỢT QUA HEALTH CHECK!")
    print(f">> Đang mở trình duyệt tại: {dev_url}")
    print(">> Nhấn Ctrl + C để dừng phiên làm việc an toàn.")
    print("=" * 65)

    try:
        webbrowser.open(dev_url)
    except Exception:
        pass

    try:
        while True:
            time.sleep(2)
            for item in list(SPAWNED_PROCESSES):
                name, proc = item
                if proc.poll() is not None:
                    print(f"\n[!] CẢNH BÁO: Dịch vụ '{name}' đã dừng đột ngột (Exit Code: {proc.returncode})!")
                    SPAWNED_PROCESSES.remove(item)
    except KeyboardInterrupt:
        print("\n>> Nhận tín hiệu ngắt (Ctrl+C)...")
    finally:
        clean_shutdown()
    return True


def run_prod_mode():
    """Executes Production Mode: Port 8000 (Serving dist) & Port 18020."""
    print("\n" + "=" * 65)
    print("   KHỞI CHẠY HỆ THỐNG - CHẾ ĐỘ VẬN HÀNH (PRODUCTION MODE)")
    print("=" * 65)
    print(">> Dịch vụ yêu cầu:")
    print("   1. DashBoardD Web & API Server : http://localhost:8000")
    print(f"   2. Test Engine Backend         : http://localhost:18020 ({TEST_DIR})")
    print("-" * 65)

    # Verify frontend dist exists
    if not os.path.exists(DASHBOARD_DIST_INDEX):
        print("   [!] THÔNG BÁO: Thư mục 'dist' chưa được biên dịch.")
        print("   Đang tiến hành build production frontend (npm run build)...")
        npm_path = shutil.which("npm.cmd") or shutil.which("npm")
        if not npm_path:
            print("   [!] LỖI: Không tìm thấy npm để build frontend. Hủy quy trình.")
            return False
        res = subprocess.run(f'"{npm_path}" run build', cwd=DASHBOARD_FRONTEND_DIR, shell=True)
        if res.returncode != 0:
            print("   [!] LỖI: Biên dịch frontend thất bại. Hủy quy trình.")
            return False

    # 1. Start DashBoardD backend (serves both API & built dist on port 8000)
    if not start_dashboard_backend():
        print("[!] Không thể khởi động DashBoardD Backend. Hủy quy trình.")
        clean_shutdown()
        return False

    # 2. Start Test backend
    if not start_test_backend():
        print("[!] Không thể khởi động Test Engine Backend. Hủy quy trình.")
        clean_shutdown()
        return False

    prod_url = "http://localhost:8000"
    print("\n" + "=" * 65)
    print(">> HỆ THỐNG VẬN HÀNH ĐÃ SẴN SÀNG VÀ VƯỢT QUA HEALTH CHECK!")
    print(f">> Đang mở trình duyệt tại: {prod_url}")
    print(">> Nhấn Ctrl + C để dừng phiên làm việc an toàn.")
    print("=" * 65)

    try:
        webbrowser.open(prod_url)
    except Exception:
        pass

    try:
        while True:
            time.sleep(2)
            for item in list(SPAWNED_PROCESSES):
                name, proc = item
                if proc.poll() is not None:
                    print(f"\n[!] CẢNH BÁO: Dịch vụ '{name}' đã dừng đột ngột (Exit Code: {proc.returncode})!")
                    SPAWNED_PROCESSES.remove(item)
    except KeyboardInterrupt:
        print("\n>> Nhận tín hiệu ngắt (Ctrl+C)...")
    finally:
        clean_shutdown()
    return True


# ==============================================================================
# 6. INTERACTIVE MENU
# ==============================================================================
def show_menu():
    while True:
        print("\n" + "=" * 65)
        print("   UNIFIED LAUNCHER - DASHBOARDD & TEST APPLICATION")
        print("=" * 65)
        print(" [1] Khởi chạy Chế độ Phát triển (Dev Mode: Port 5174, 8000, 18020)")
        print(" [2] Khởi chạy Chế độ Vận hành (Production Mode: Port 8000, 18020)")
        print(" [3] Kiểm tra trạng thái hệ thống (Read-only Status & Health Check)")
        print(" [0] Thoát")
        print("=" * 65)
        
        try:
            choice = input("Nhập lựa chọn của bạn [0-3]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n>> Thoát.")
            break
            
        if choice == "1":
            run_dev_mode()
            break
        elif choice == "2":
            run_prod_mode()
            break
        elif choice == "3":
            run_status_check()
            input("\nNhấn Enter để quay lại menu...")
        elif choice == "0":
            print(">> Đã thoát Unified Launcher.")
            break
        else:
            print("\n[!] Lựa chọn không hợp lệ. Vui lòng nhập số từ 0 đến 3.")


def main():
    # Handle direct CLI arguments if supplied
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip()
        if arg in ["--dev", "-d", "1"]:
            run_dev_mode()
        elif arg in ["--prod", "-p", "2"]:
            run_prod_mode()
        elif arg in ["--status", "-s", "--check", "3"]:
            run_status_check()
        elif arg in ["--help", "-h"]:
            print("Cách sử dụng:")
            print("  py unified_launcher.py          (Mở Interactive Menu)")
            print("  py unified_launcher.py --dev    (Khởi chạy Dev Mode)")
            print("  py unified_launcher.py --prod   (Khởi chạy Prod Mode)")
            print("  py unified_launcher.py --status (Kiểm tra trạng thái hệ thống)")
        else:
            print(f"[!] Tham số không nhận diện: {arg}")
            print("Chạy với --help để xem hướng dẫn.")
            sys.exit(1)
    else:
        show_menu()


if __name__ == "__main__":
    main()
