@echo off
chcp 65001 >nul
title DashBoardD Server - 1 Cua So CMD
echo ========================================================
echo   DashBoardD Server - Mang Noi Bo Doanh Nghiep
echo ========================================================
echo.

:: 1. Giai phong cong 8000 neu truoc do bi treo hoac dang bi chiem dung
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Dang giai phong cong 8000 tu tien trinh PID %%a...
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo ========================================================
echo DUONG DAN TRUY CAP (Luu Bookmark tren trinh duyet):
echo.
echo 👉 Link Dashboard:        http://10.96.25.111:8000
echo 👉 Trang Quan Tri Admin:   http://10.96.25.111:8000/#/admin
echo ========================================================
echo.
echo Dang khoi dong server tren cong 8000...
echo (Vui long giu cua so CMD nay de he thong hoat dong)
echo.

cd /d "%~dp0backend"
"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
