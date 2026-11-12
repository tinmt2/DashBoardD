@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
echo =================================================================
echo  KHỞI CHẠY CÔNG CỤ XOAY VÒNG CREDENTIAL ADMIN (PHASE 6B)
echo =================================================================
py -3.12 scripts\rotate_admin_credentials.py
pause
