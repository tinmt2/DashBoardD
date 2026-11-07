@echo off
title DashBoardD Unified Server (1 Server Port 8000)
cd /d "%~dp0"
echo ========================================================
echo   Khoi dong DashBoardD - 1 Server duy nhat (Port 8000)
echo ========================================================

REM Kiem tra neu dist chua co thi build
if not exist "dashboard-app\dist\index.html" (
    echo [1/2] Dang build Frontend lan dau...
    call npm --prefix dashboard-app run build
)

echo [2/2] Dang chay Server tai http://localhost:8000 ...
cd backend
py -3.12 -m uvicorn app.main:app --port 8000 --reload
pause
