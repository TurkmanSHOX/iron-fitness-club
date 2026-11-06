# TASHQI INTEGRATSIYALAR VA MAXFIY PARAMETRLAR RO'YXATI

Hozirgi vaqtda tizim lokal va mustaqil (off-grid) rejimda to'liq ishlamoqda. Real Telegram Bot va onlayn to'lov tizimlarini (Click / Payme) jonlantirish uchun quyidagi parametrlar `.env` fayliga kiritilishi kerak:

---

## 1. TELEGRAM BOT PARAMETRLARI

| Parametr | Tavsif | Qayerdan olinadi? |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Botning rasmiy API kaliti | Telegramda [@BotFather](https://t.me/BotFather) ga `/newbot` buyrug'ini yuborib olinadi. Masalan: `7891234567:AAFl...` |
| `TELEGRAM_BOT_USERNAME` | Botning username nomi | Masalan: `iron_fitness_club_bot` |
| `ADMIN_TELEGRAM_ID` | Xabarnomalar borishi kerak bo'lgan bosh admin Telegram ID raqami | Telegramda [@userinfobot](https://t.me/userinfobot) orqali bilib olinadi. Masalan: `123456789` |

**Botni ishga tushirish:**
```bash
python bot/bot.py
```

---

## 2. CLICK INTEGRATSIYASI

| Parametr | Tavsif | Qayerdan olinadi? |
|---|---|---|
| `CLICK_MERCHANT_ID` | Click tizimidagi korxona ID si | Click Merchant kabinetidan |
| `CLICK_SERVICE_ID` | Xizmat ID raqami | Click Merchant kabinetidan |
| `CLICK_SECRET_KEY` | Tranzaksiya MD5 imzosini tekshirish uchun maxfiy kalit | Click shartnoma tuzilgach beriladi |

* **Click Webhook manzillari:**
  - Prepare URL: `https://sizning-domeningiz.uz/click/prepare`
  - Complete URL: `https://sizning-domeningiz.uz/click/complete`

---

## 3. PAYME INTEGRATSIYASI

| Parametr | Tavsif | Qayerdan olinadi? |
|---|---|---|
| `PAYME_MERCHANT_ID` | Payme Business dagi ID raqam | Payme Business (merchant.paycom.uz) kabinetidan |
| `PAYME_SECRET_KEY` | Basic Auth maxfiy kaliti | Payme shartnoma tuzilgach beriladi |
| `PAYME_TEST_MODE` | Test rejimi | Sinov davrida `true`, real ishda `false` |

* **Payme Webhook manzili:**
  - Endpoint: `https://sizning-domeningiz.uz/payme`
  - Protokol: `JSON-RPC 2.0` (Basic Auth)

---

## 4. YANGILANGAN `.env.example` SHABLONI

```env
# XAVFSIZLIK
SECRET_KEY=kamida-32-belgidan-iborat-kriptografik-kuchli-maxfiy-kalit-2026

# MA'LUMOTLAR BAZASI
DATABASE_URL=mysql+pymysql://root:@localhost:3306/iron_fitness_club?charset=utf8mb4
TIMEZONE=Asia/Tashkent

# TELEGRAM BOT
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_USERNAME=iron_fitness_club_bot
ADMIN_TELEGRAM_ID=

# CLICK MERCHANT
CLICK_MERCHANT_ID=
CLICK_SERVICE_ID=
CLICK_SECRET_KEY=

# PAYME MERCHANT
PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=
PAYME_TEST_MODE=true

# SERVER
PORT=5000
HOST=0.0.0.0
DEBUG=False
FLASK_ENV=production
```
