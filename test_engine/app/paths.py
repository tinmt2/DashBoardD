import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS (for onefile) or sys.executable dir.
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
RUNTIME_DIR = Path(app_data) / "test_app" / "runtime"
CHROME_PROFILE_DIR = RUNTIME_DIR / "chrome_profile"
TOKEN_FILE = RUNTIME_DIR / "token.txt"

# External Log Storage setup
PRIMARY_LOGS_DIR = Path(r"D:\test_app_logs")
FALLBACK_LOGS_DIR = RUNTIME_DIR / "logs"

def get_log_dir() -> Path:
    try:
        PRIMARY_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = PRIMARY_LOGS_DIR / ".write_test"
        test_file.touch(exist_ok=True)
        test_file.unlink()
        return PRIMARY_LOGS_DIR
    except Exception as e:
        print(f"LOG_STORAGE_FALLBACK: Unable to write logs to {PRIMARY_LOGS_DIR}, using fallback runtime log directory. Error: {e}")
        return FALLBACK_LOGS_DIR

LOGS_DIR = get_log_dir()

def ensure_runtime_dirs():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
