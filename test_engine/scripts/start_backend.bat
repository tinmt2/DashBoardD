@echo off
setlocal
cd /d "%~dp0\.."

set VENV_PYTHON="%~dp0..\.venv\Scripts\python.exe"

if not exist %VENV_PYTHON% (
    echo [ERROR] Khong tim thay Python ao tai: %VENV_PYTHON%
    echo Vui long kiem tra lai thu muc .venv.
    pause
    exit /b 1
)

echo [INFO] Dang khoi chay Test-LC Backend doc lap tren port 18020...
%VENV_PYTHON% scripts\dev\run_standalone_backend.py

if errorlevel 1 (
    echo [ERROR] Backend dung voi ma loi %errorlevel%.
    pause
    exit /b %errorlevel%
)

exit /b 0
