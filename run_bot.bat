@echo off
chcp 65001 > nul
title IRON FITNESS CLUB - Telegram Bot
echo =====================================================================
echo           IRON FITNESS CLUB TELEGRAM BOTI ISHGA TUSHMOQDA
echo =====================================================================
echo.

if not exist venv\Scripts\python.exe (
    echo [XATOLIK] Virtual muhit (venv) topilmadi!
    pause
    exit /b
)

echo Botni to'xtatish uchun Ctrl+C bosing.
echo =====================================================================
echo.

venv\Scripts\python.exe bot\bot.py
pause
