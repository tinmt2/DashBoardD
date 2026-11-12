import os
import subprocess
import sys

def main():
    print("--- Building Backend with PyInstaller ---")
    
    # Ensure pyinstaller is installed
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    args = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "backend",
        "--add-data", "app;app",
        "app/api/main.py"
    ]
    
    print("Running command:", " ".join(args))
    result = subprocess.run(args, capture_output=False)
    if result.returncode == 0:
        print("Backend build successful!")
    else:
        print("Backend build failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
