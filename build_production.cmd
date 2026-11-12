@echo off
setlocal
title DashBoardD Build Production
cd /d "%~dp0"

echo ========================================================
echo   CAP NHAT CODE MOI LEN WEB CHINH (PORT 8000)
echo ========================================================
echo.
echo [+] Dang build dong goi code tu src sang dist...
echo.

npm --prefix dashboard-app run build

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo [THANH CONG] Da build xong thu muc dist!
    echo Web chinh (:8000) da tu dong cap nhat giao dien moi.
    echo ========================================================
) else (
    echo.
    echo [LOI] Build that bai, vui long kiem tra lai code.
)

echo.
pause
