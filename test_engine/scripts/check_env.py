import sys
import os
import subprocess
import shutil

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return res.stdout.strip()
        else:
            return f"Error: {res.stderr.strip()}"
    except Exception as e:
        return f"Failed to execute: {str(e)}"

def check():
    print("========================================")
    print("       ENVIRONMENT CHECK SCRIPT")
    print("========================================")
    
    # 1. Python
    print(f"Python Version: {sys.version.split(' ')[0]} - [PASS]")
    
    # 2. Pip
    pip_v = run_cmd(["pip", "--version"])
    print(f"pip: {pip_v.split(' ')[0] if not pip_v.startswith('Failed') else pip_v} - [{'PASS' if 'pip' in pip_v else 'MISSING'}]")
    
    # 3. Chrome
    # This is tricky on Windows, let's try querying registry or just look for the executable
    chrome_path = None
    for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
        if os.path.exists(p):
            chrome_path = p
            break
    if chrome_path:
        print(f"Chrome: Found at {chrome_path} - [PASS]")
    else:
        print("Chrome: Not found in default paths - [MISSING/FAIL]")
        
    # 4. ChromeDriver
    chromedriver = shutil.which("chromedriver")
    if chromedriver:
        print(f"ChromeDriver: Found in PATH ({chromedriver}) - [PASS]")
    else:
        print("ChromeDriver: Not found in PATH - [MISSING/FAIL]")
        
    # 5. Selenium
    try:
        import selenium
        print(f"Selenium: v{selenium.__version__} - [PASS]")
    except ImportError:
        print("Selenium: Not installed - [MISSING/FAIL]")
        
    # 6. FastAPI
    try:
        import fastapi
        print(f"FastAPI: v{fastapi.__version__} - [PASS]")
    except ImportError:
        print("FastAPI: Not installed - [MISSING/FAIL]")
        
    print("========================================")
    print("Check complete. Please ensure backend is running before executing ftel_real_e2e.py.")

if __name__ == "__main__":
    check()
