@echo off
chcp 65001 >nul
title DashBoardD (Port 8000 + Ngrok) - 1 Cua So CMD
cd /d "%~dp0"
"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" run_all_in_one.py
pause
