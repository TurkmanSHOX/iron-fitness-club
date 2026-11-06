@echo off
chcp 65001 >nul
title IRON FITNESS CLUB — Avtomatik Zaxiralash Rejasini O'rnatish
color 0B

echo =====================================================================
echo       IRON FITNESS CLUB — AVTOMATIK ZAXIRALASH REJASINI SOZLASH
echo =====================================================================
echo.
echo Ushbu skript har kuni soat 23:00 da MariaDB ma'lumotlar bazasidan
echo avtomatik zaxira nusxasi (.sql.gz) olib, 'backups/' katalogiga
echo saqlash vazifasini Windows Rejalashtiruvchisiga (Task Scheduler) kiritadi.
echo.

set PYTHON_PATH=%~dp0..\venv\Scripts\python.exe
set BACKUP_SCRIPT=%~dp0backup.py

if not exist "%PYTHON_PATH%" (
    echo [XATOLIK] Python virtual muhiti topilmadi: %PYTHON_PATH%
    pause
    exit /b 1
)

echo Rejalashtirilgan vazifa yaratilmoqda...
schtasks /create /tn "IronFitness_Daily_Backup" /tr "\"%PYTHON_PATH%\" \"%BACKUP_SCRIPT%\" auto" /sc daily /st 23:00 /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo [MUVAFFAQIYATLI] "IronFitness_Daily_Backup" vazifasi muvaffaqiyatli rejalashtirildi!
    echo Har kuni soat 23:00 da avtomatik zaxiralash bajariladi.
) else (
    echo.
    echo [OGOHLANTIRISH] Administrator huquqi talab qilinishi mumkin.
    echo Iltimos, ushbu faylni "Administrator nomidan ishga tushirish" (Run as administrator) orqali oching.
)

echo.
pause
