@echo off
chcp 65001 >nul
title IRON FITNESS CLUB — MariaDB Avtomatik Ishga Tushishini Sozlash
color 0B

echo =====================================================================
echo       MARIADB AVTOMATIK ISHGA TUSHISHINI SOZLASH (AUTO-START)
echo =====================================================================
echo.
echo Ushbu skript kompyuter yoqilganda MariaDB serverining avtomatik
echo orqa fonda ishga tushishini ta'minlaydi.
echo.

set MYSQLD_PATH=C:\Users\avemo\mariadb\bin\mysqld.exe
set DATA_DIR=C:\Users\avemo\mariadb\data

if not exist "%MYSQLD_PATH%" (
    echo [XATOLIK] MariaDB serveri topilmadi: %MYSQLD_PATH%
    pause
    exit /b 1
)

echo Windows xizmati (Service) sifatida ro'yxatdan o'tkazishga urinilmoqda...
"%MYSQLD_PATH%" --install MariaDB --datadir="%DATA_DIR%" --port=3306

if %ERRORLEVEL% equ 0 (
    echo [OK] MariaDB Windows xizmati sifatida muvaffaqiyatli o'rnatildi!
    sc config MariaDB start= auto
    net start MariaDB
    echo [MUVAFFAQIYATLI] MariaDB xizmati avtomatik ishga tushish rejimiga o'tkazildi!
) else (
    echo.
    echo [MUQOBIL USUL] Administrator huquqi bo'lmasa, Windows Rejalashtiruvchisi ishlatiladi:
    schtasks /create /tn "IronFitness_MariaDB_Autostart" /tr "\"%MYSQLD_PATH%\" --datadir=\"%DATA_DIR%\" --port=3306" /sc onstart /ru SYSTEM /f >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo [OK] Windows Rejalashtiruvchisida avtomatik ishga tushirish muvaffaqiyatli saqlandi.
    ) else (
        echo [OGOHLANTIRISH] Iltimos, ushbu faylni "Administrator nomidan ishga tushirish" orqali oching.
    )
)

echo.
pause
