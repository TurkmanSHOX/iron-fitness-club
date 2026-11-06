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

echo [1/2] Flask veb-server ishga tushirilmoqda...
echo.
echo Veb-panel: http://127.0.0.1:5000
echo Login:     admin
echo Parol:     admin123
echo.
echo Serverni to'xtatish uchun Ctrl+C bosing.
echo =====================================================================
echo.

venv\Scripts\python.exe run.py
pause
