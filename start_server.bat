@echo off
title DashBoardD Production Server
echo ==============================================
echo   DashBoardD Server - FPT Shop / Long Chau
echo ==============================================
echo.
echo IP mang noi bo cua ban (chia se link nay):
for /f "tokens=14" %%a in ('ipconfig ^| findstr IPv4') do echo http://%%a:8000
echo.
echo ==============================================
echo Dang khoi dong server... Vui long khong tat cua so nay.
cd backend
"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
