@echo off
chcp 65001 >nul
title DashBoardD Server - https://tonghoploi.loca.lt
echo ========================================================
echo   DashBoardD Server - Ten Mien https://tonghoploi.loca.lt
echo ========================================================
echo.

:: 1. Don dep tien trinh tunnel cu neu co de tranh bi trung ten mien
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name = 'node.exe'\" | Where-Object { $_.CommandLine -like '*tunnel_runner.js*' -or $_.CommandLine -like '*localtunnel*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: 2. Kiem tra va khoi dong backend tren cong 8000
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% neq 0 (
    echo Dang khoi dong Backend DashBoardD tren cong 8000...
    start "DashBoardD Backend (Port 8000)" cmd /c "cd /d %~dp0backend && \"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe\" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    timeout /t 3 /nobreak >nul
) else (
    echo Backend tren cong 8000 da dang chay san sang!
)

echo.
echo ========================================================
echo   DANG KET NOI TEN MIEN CO DINH: https://tonghoploi.loca.lt
echo   (Neu lan truoc vua dong xong mo lai ngay, he thong se
echo    tu dong thu lai vai giay de lay dung ten mien nay)
echo ========================================================
echo.

cd /d "%~dp0"
node tunnel_runner.js tonghoploi 8000
pause
