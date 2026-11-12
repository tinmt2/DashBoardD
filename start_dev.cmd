@echo off
setlocal
title DashBoardD Dev Server (Port 5174)
cd /d "%~dp0"

echo ========================================================
echo   DashBoardD - DEV SERVER (PORT 5174)
echo ========================================================
echo.
echo [INFO] Web chinh van chay tai http://localhost:8000
echo [INFO] Dang khoi dong Web Dev tai http://localhost:5174
echo.

start "" http://localhost:5174
npm --prefix dashboard-app run dev
pause
