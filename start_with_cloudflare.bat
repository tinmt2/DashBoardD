@echo off
chcp 65001 >nul
title DashBoardD + Cloudflare Tunnel (1 Cua So CMD)
cd /d "%~dp0"
"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" run_cloudflare_in_one.py
pause
