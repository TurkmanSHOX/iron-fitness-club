@echo off
chcp 65001 > nul
title IRON FITNESS CLUB - Server
echo =====================================================================
echo                IRON FITNESS CLUB BOSHQARUV TIZIMI
echo =====================================================================
echo.

if not exist venv\Scripts\python.exe (
    echo [XATOLIK] Virtual muhit (venv) topilmadi!
    pause
    exit /b
)

echo [1/2] Production WSGI server (Waitress) ishga tushirilmoqda...
echo.
echo Veb-panel manzili: http://127.0.0.1:5000
echo Eslatma: Dastlabki kirishda tizim xavfsizlik uchun parolni yangisiga almashtirishni majburiy talab qiladi.
echo.
echo Serverni to'xtatish uchun Ctrl+C bosing.
echo =====================================================================
echo.

venv\Scripts\python.exe wsgi.py
pause
