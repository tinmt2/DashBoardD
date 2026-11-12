@echo off
setlocal
title Unified Launcher - DashBoardD ^& Test Engine
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3.12 unified_launcher.py %*
    goto :end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python unified_launcher.py %*
    goto :end
)

echo [ERROR] Khong tim thay Python tren he thong!
echo Vui long cai dat Python 3.12 de tiep tuc.
pause
exit /b 1

:end
exit /b %errorlevel%
