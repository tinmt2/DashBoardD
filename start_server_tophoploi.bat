@echo off
chcp 65001 >nul
title DashBoardD - https://tophoploi.site (1 Cua So CMD)
cd /d "%~dp0"

:loop
"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" run_tophoploi_tunnel.py
echo.
echo [!] Server da dung. Tu dong khoi dong lai sau 2 giay... (Nhan Ctrl+C de thoat)
timeout /t 2 >nul
goto loop
