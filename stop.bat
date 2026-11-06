@echo off
chcp 65001 >nul
title IRON FITNESS CLUB — Tizimni To'xtatish
color 0C

echo =====================================================================
echo                IRON FITNESS CLUB — TIZIMNI TO'XTATISH
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Flask serverini to'xtatish (5000-portda ishlayotgan jarayon)
echo [1/2] Flask veb-serveri (5000-port) to'xtatilmoqda...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    echo [OK] Flask jarayoni (PID: %%a) to'xtatildi.
)

:: 2. MariaDB ni to'xtatish variantini so'rash
echo.
set /p stop_db="MariaDB ma'lumotlar bazasini ham to'xtatasizmi? (ha/yo'q, standart: yo'q): "
if /i "%stop_db%"=="ha" (
    echo MariaDB serveri to'xtatilmoqda...
    if exist "C:\Users\avemo\mariadb\bin\mysqladmin.exe" (
        "C:\Users\avemo\mariadb\bin\mysqladmin.exe" -u root shutdown >nul 2>&1
    )
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3306 ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    echo [OK] MariaDB to'xtatildi.
) else (
    echo [INFO] MariaDB orqa fonda ishlashda qoldirildi (tavsiya etiladi).
)

echo.
echo =====================================================================
echo Tizim muvaffaqiyatli to'xtatildi.
echo =====================================================================
timeout /t 3
