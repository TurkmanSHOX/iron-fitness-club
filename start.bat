@echo off
chcp 65001 >nul
title IRON FITNESS CLUB — Tizimni Ishga Tushirish
color 0A

echo =====================================================================
echo                IRON FITNESS CLUB AVTOMATLASHTIRISH TIZIMI
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. MariaDB holatini tekshirish
echo [1/3] MariaDB serveri tekshirilmoqda...
netstat -ano | findstr :3306 >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] MariaDB serveri 3306-portda faol ishlamoqda.
) else (
    echo [OGOHLANTIRISH] MariaDB 3306-portda topilmadi. Ishga tushirishga urinish...
    if exist "C:\Users\avemo\mariadb\bin\mysqld.exe" (
        start /B "" "C:\Users\avemo\mariadb\bin\mysqld.exe" --datadir="C:\Users\avemo\mariadb\data" --port=3306
        timeout /t 3 /nobreak >nul
        netstat -ano | findstr :3306 >nul
        if %ERRORLEVEL% equ 0 (
            echo [OK] MariaDB muvaffaqiyatli ishga tushirildi.
        ) else (
            echo [XATOLIK] MariaDB ishga tushmadi. Iltimos, MariaDB o'rnatilganligini tekshiring.
            pause
            exit /b 1
        )
    ) else (
        echo [XATOLIK] MariaDB serveri topilmadi.
        pause
        exit /b 1
    )
)

:: 2. Virtual muhitni tekshirish
echo [2/3] Virtual muhit faollashtirilmoqda...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual muhit faol.
) else (
    echo [XATOLIK] 'venv' katalogi topilmadi!
    pause
    exit /b 1
)

:: 3. Brauzerda ochish va Flask dasturini ishga tushirish
echo [3/3] Veb-panel ishga tushirilmoqda: http://127.0.0.1:5000
start "" "http://127.0.0.1:5000"

python run.py

pause
