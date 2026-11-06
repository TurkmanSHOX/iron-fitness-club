# IRON FITNESS CLUB — Sport Zalini Avtomatlashtirish Tizimi

**IRON FITNESS CLUB** fitnes zali faoliyatini to‘liq raqamlashtiruvchi, xavfsiz va zamonaviy veb-boshqaruv hamda Telegram bot tizimi.

Ushbu tizim `IRON_FITNESS_CLUB_Texnik_Topshiriq.docx` texnik topshirig‘iga 100% muvofiq ravishda ishlab chiqilgan.

---

## 🛠 Texnologiyalar

| Tarkibiy qism | Texnologiya |
| :--- | :--- |
| **Backend** | Python 3.12, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF |
| **Ma’lumotlar bazasi** | MariaDB / MySQL (HeidiSQL orqali to‘liq boshqariladi) |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, FontAwesome 6 |
| **Telegram Bot** | Python aiogram 3.x (Asyncio) |
| **Grafik & Statistika** | Chart.js |
| **QR & Shtrix-kod** | 2D Barcode / QR Scanner, Python `qrcode` & `Pillow` |
| **Cheklar & Hujjatlar** | ReportLab (PDF Elektron kassa cheklari) |
| **Hisobotlar** | OpenPyXL (Excel eksport), Pandas |
| **Rejalashtiruvchi** | APScheduler (Abonement eslatmalari va avto-muzlatish) |
| **To‘lov integratsiyasi**| Click va Payme rasmiy Merchant Webhook adapterlari |
| **Vaqt mintaqasi** | Asia/Tashkent |

---

## 📂 Loyiha Tuzilmasi

```text
IRON_FITNESS_CLUB/
├── app/
│   ├── models/             # MariaDB SQLAlchemy modellari (Admin, Client, Tariff, Subscription, POS...)
│   ├── routes/             # Blueprint routerlar (Auth, Dashboard, Scanner, POS, Inventory, Reports...)
│   ├── services/           # Asosiy biznes mantiq (QR kirish, Muzlatish, POS savdo, Click/Payme, PDF...)
│   ├── forms/              # Flask-WTF formalar
│   ├── templates/          # Bootstrap 5 shablonlari (#255F38 to'q yashil va #99BC85 och yashil)
│   ├── static/             # CSS, JS, rasmlar
│   ├── config.py           # Muhit sozlamalari
│   ├── extensions.py       # SQLAlchemy, LoginManager, APScheduler
│   └── __init__.py         # Ilova fabrikasi (create_app)
├── bot/
│   ├── handlers/           # Telegram bot handlerlari (Ro'yxatdan o'tish, QR kod, Muzlatish, Tarix...)
│   ├── keyboards/          # Reply va Inline tugmalar
│   └── bot.py              # Aiogram 3 bot ishga tushirish skripti
├── database/
│   ├── schema.sql          # MariaDB / HeidiSQL uchun to'liq DDL sxemasi (25 ta jadval)
│   └── seed.sql            # Dastlabki admin, 4 ta tarif, tovarlar va sozlamalar
├── tests/
│   └── test_iron_fitness.py# 8 ta to'liq avtomatlashtirilgan testlar (100% o'tgan)
├── uploads/                # Mijoz rasmlari, QR-kodlar, cheklar va xarajat rasmlari
├── reports/                # Generatsiya qilingan Excel hisobotlar
├── backups/                # Ma'lumotlar bazasi avtomatik zaxira nusxalari
├── .env.example            # Muhit o'zgaruvchilari namunasi
├── requirements.txt        # Barcha Python kutubxonalari
├── run.py                  # Flask server ishga tushirish fayli
├── run.bat                 # Windows tezkor start skripti
├── run_bot.bat             # Telegram bot tezkor start skripti
└── USER_GUIDE.md           # Administrator foydalanish qo'llanmasi
```

---

## 🚀 O‘rnatish va Ishga Tushirish

### 1. Talablar
- Python 3.10+ (tavsiya etiladi: Python 3.12)
- MariaDB yoki MySQL server (yoki dastlabki sinov uchun avtomatik SQLite)
- HeidiSQL (Ma'lumotlar bazasini qulay boshqarish uchun)

### 2. O‘rnatish qadamlari

```bash
# 1. Virtual muhit yaratish va faollashtirish
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 3. .env faylini sozlash
copy .env.example .env
```

### 3. Ma’lumotlar bazasini sozlash (HeidiSQL / MariaDB)

1. **HeidiSQL** dasturini oching va MariaDB serveringizga ulaning.
2. `database/schema.sql` faylini ochib, uni to‘liq ishga tushiring (F9).
3. `database/seed.sql` faylini ishga tushiring.
4. `.env` faylida ulanish manzilini ko‘rsating:
   ```env
   DATABASE_URL=mysql+pymysql://root:parol@localhost:3306/iron_fitness_club?charset=utf8mb4
   ```

*(Eslatma: Agar kompyuteringizda hozircha MariaDB o‘rnatilmagan bo‘lsa, tizim avtomatik ravishda `instance/iron_fitness.db` bilan to‘liq ishlayveradi).*

### 4. Serverni ishga tushirish

Windows uchun:
```cmd
run.bat
```
Yoki terminalda:
```bash
python run.py
```
Brauzerda oching: **`http://127.0.0.1:5000`**

- **Standart login:** `admin`
- **Standart parol:** `admin123`

---

## 🤖 Telegram Botni Ishga Tushirish

1. [@BotFather](https://t.me/BotFather) orqali yangi bot oching va tokenini oling.
2. `.env` faylidagi `TELEGRAM_BOT_TOKEN` parametriga tokenni yozing:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCDEfghIjk...
   ```
3. Botni ishga tushiring:
   ```bash
   python bot/bot.py
   # Yoki Windowsda: run_bot.bat
   ```

---

## 🧪 Avtomatlashtirilgan Testlarni O‘tkazish

Tizimdagi barcha funksiyalar va biznes qoidalar `pytest` orqali to‘liq qamrab olingan:

```bash
pytest tests/test_iron_fitness.py -v
```

**Test qamrovi:**
- `test_admin_auth`: Admin login, parollarni xavfsiz xeshlash;
- `test_tariffs_and_client_creation`: 4 ta boshlang‘ich tarif va xavfsiz yagona QR-kod ishlab chiqarish;
- `test_subscription_date_calculation`: Kalendar oylari va 31-yanvar $\rightarrow$ 28-fevral qoidasi;
- `test_access_control_and_scanner`: Juft/toq kunlar, 2D skaner ruxsat va rad etishi, takroriy kirish bloklanishi va istisno ruxsati;
- `test_freeze_request_and_extension`: Muzlatish so‘rovi, admin tasdig‘i, muddat uzaytirilishi va kirish taqiqlanishi;
- `test_pos_and_inventory_integration`: 2D skaner POS savdosi, ombor qoldig‘ining kamayishi, manfiy qoldiqqa yo‘l qo‘yilmasligi va qaytarish (refund);
- `test_payment_webhooks`: Click va Payme webhook imzolari, idempotency va abonement avto-faollashishi;
- `test_pdf_and_excel_generation`: Elektron PDF kassa cheki, QR-kod rasmlari va professional Excel hisoboti.

---

## 💳 To‘lov Integratsiyalari Sozlamasi

1. **Click:**
   - Prepare URL: `https://sizning-saytingiz.uz/api/click/prepare`
   - Complete URL: `https://sizning-saytingiz.uz/api/click/complete`
2. **Payme:**
   - Endpoint URL: `https://sizning-saytingiz.uz/api/payme`
   - HTTP Basic Auth: Login `Paycom`, Parol: `.env` dagi `PAYME_SECRET_KEY`.

---

## 📄 Litsenziya

IRON FITNESS CLUB &copy; 2026. Barcha huquqlar himoyalangan.
