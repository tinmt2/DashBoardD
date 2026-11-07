import os
import sys
import subprocess
import signal
import time

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "dashboard-app")

    print("=" * 65)
    print("   DashBoardD - Khoi dong Fullstack (1 CMD duy nhat)")
    print("=" * 65)
    print(">> [1/2] Backend API : http://localhost:8000")
    print(">> [2/2] Frontend App: http://localhost:5174")
    print(">> Nhan Ctrl + C de dung ca 2 server cung luc.")
    print("=" * 65)

    # 1. Start Backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=backend_dir
    )

    # 2. Start Frontend
    frontend_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir,
        shell=True
    )

    try:
        while True:
            # Check if any process terminated unexpectedly
            if backend_proc.poll() is not None:
                print(">> Backend da dung.")
                break
            if frontend_proc.poll() is not None:
                print(">> Frontend da dung.")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n>> Dang tat ca 2 server...")
    finally:
        # Clean shutdown both processes on Windows
        try:
            if frontend_proc.poll() is None:
                subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        try:
            if backend_proc.poll() is None:
                subprocess.run(f"taskkill /F /T /PID {backend_proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        print(">> Da dung thanh cong.")

if __name__ == "__main__":
    main()
