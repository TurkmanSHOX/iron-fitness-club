# IRON FITNESS CLUB — ADMINISTRATOR FOYDALANISH QO'LLANMASI

Ushbu qo'llanma **IRON FITNESS CLUB** sport majmuasi ma'muriyati (administratorlar, reception xodimlari va kassa operatorlari) uchun kundalik faoliyatni to'liq avtomatlashtirilgan tizimda samarali va xatosiz yuritish maqsadida ishlab chiqilgan.

---

## 1. TIZIMNI ISHGA TUSHIRISH VA KIRISH

### 1.1 Dasturni ishga tushirish:
1. Ish stolida (Desktop) joylashgan `start.bat` faylini ikki marta bosing.
2. Tizim avtomatik tarzda MariaDB ma'lumotlar bazasi va dastur muhitini tekshiradi hamda brauzerda `http://127.0.0.1:5000` manzilini ochadi.
3. Dasturni to'xtatish uchun `stop.bat` faylidan foydalaning.

### 1.2 Tizimga kirish va birinchi parol:
* **Kirish manzili:** `http://127.0.0.1:5000/login`
* **Dastlabki login:** `admin`
* **Dastlabki parol:** `admin123`
* **Xavfsizlik talabi:** Birinchi marta tizimga kirganingizda, tizim xavfsizligini ta'minlash uchun darhol parolni o'zingizning yangi shaxsiy parolingizga almashtirishingiz shart.

---

## 2. MIJOZLARNI RO'YXATGA OLISH VA QR-KOD BERISH

1. Chap menyudan **"Mijozlar"** bo'limiga kiring va **"+ Yangi mijoz"** tugmasini bosing.
2. Quyidagi ma'lumotlarni to'ldiring:
   - **F.I.O:** Mijozning to'liq ismi (masalan: *Anvar Karimov*).
   - **Telefon raqami:** Telefon raqami yagona bo'lishi shart (`+998901234567` formatida).
   - **Tug'ilgan sana va jinsi:** Mijoz statistikasi uchun.
   - **Surat (Ixtiyoriy):** Mijozning fotosuratini yuklang.
3. **"Saqlash"** tugmasini bosing.
4. Tizim mijoz uchun noyob **16 belgili shaxsiy QR-kod** ishlab chiqadi.
5. Mijoz kartasida **"QR-kodni yuklab olish"** tugmasi orqali QR-kod rasmini yuklab olib, reception printeridan plastik karta yoki qog'oz shaklida chop etib mijozga taqdim etishingiz mumkin.

---

## 3. ABONEMENT SOTISH VA TO'LOV QABUL QILISH

1. **"Abonementlar"** bo'limiga o'ting va **"+ Abonement sotish"** tugmasini bosing.
2. Mijozni tanlang (ismi yoki telefoni orqali qidirish).
3. Kerakli tarifni tanlang:
   - **1 kunlik tashrif:** 20 000 so'm (Bir martalik kirish).
   - **1 oylik — Juft kunlar:** 300 000 so'm (Oyning 2, 4, 6... sanalarida 30 kun kirish).
   - **1 oylik — Toq kunlar:** 300 000 so'm (Oyning 1, 3, 5... sanalarida 30 kun kirish).
   - **1 oylik — Har kuni:** 400 000 so'm (Cheklovsiz, oyning barcha kunlarida kirish).
4. **Boshlanish sanasi:** Standart bugungi sana, zarur bo'lsa kelgusi sanani belgilang.
5. **To'lov usuli:** Naqd pul (`cash`), Bank kartasi (`card`), Click yoki Payme.
6. **To'lov summasi:** Mijoz to'lagan summani kiriting va **"Tasdiqlash"** tugmasini bosing.
7. To'lov qabul qilingach, abonement darhol **"Faol" (Active)** holatga o'tadi va PDF to'lov kvitansiyasi shakllanadi.

---

## 4. 2D QR-SKANER ORQALI ZALGA KIRITISH TARTIBI

### 4.1 Skanerni tayyorlash:
- Standart USB 2D QR-skanerni kompyuterning USB portiga ulang (drayver talab qilinmaydi, Windows uni avtomatik klaviatura sifatida taniydi).
- Brauzerda **"QR Skaner"** bo'limini (`http://127.0.0.1:5000/visits/scanner`) doimo ochiq qoldiring.

### 4.2 Skanerlash jarayoni:
- Mijoz o'zining QR-kodini (plastik kartasi yoki Telegram botdagi QR-kodini) skaner oldiga tutadi.
- Tizim 0.1 soniyada quyidagi qoidalarni tekshiradi:
  * **Yashil belgi (Ruxsat):** Abonement faol, to'langan, bugungi kunga mos va bugun hali kirmagan bo'lsa — ruxsat beriladi va tashriflar jurnaliga yoziladi.
  * **Qizil belgi (Rad etish):** 
    - *Muddati tugagan* — yangilash talab etiladi.
    - *To'lov qilinmagan* — to'lov kutilmoqda.
    - *Muzlatilgan* — ayni paytda abonement to'xtatilgan.
    - *Juft/Toq kun xatoligi* — masalan, juft kunlik tarif egasi toq kunda kelgan.
    - *Qayta kirish* — mijoz bugun allaqachon bir marta kirib bo'lgan.

### 4.3 Administrator istisno ruxsati (Override):
Agar mijoz kartasini unutib qoldirgan bo'lsa yoki favqulodda ruxsat zarur bo'lsa, administrator **"Qo'lda kiritish"** tugmasini bosib, sababini (masalan: *"Karta uyda qolgan, shaxsi tasdiqlandi"*) ko'rsatgan holda kiritishi mumkin. Bu amal darhol xavfsizlik audit jurnaliga qayd etiladi.

---

## 5. ABONEMENTLARNI MUZLATISH (FREEZE)

1. Agar mijoz safarga ketsa yoki kasal bo'lsa, **10 kungacha** abonementni muzlatish huquqiga ega.
2. Mijoz kartasidan yoki **"Muzlatish so'rovlari"** bo'limidan muzlatish boshlanish va tugash sanalarini belgilang.
3. Muzlatilgan davrda mijoz zalga kira olmaydi.
4. Muzlatish muddati tugashi bilan tizim abonementni **avtomatik muzlatishdan chiqaradi** va abonementning tugash sanasini **muzlatilgan kunlar soniga uzaytiradi**.

---

## 6. KASSA VA SAVDO (POS) MODULI

1. **"Savdo va Kassa"** bo'limiga o'ting.
2. Shtrix-kod skaneri orqali mahsulot shtrix-kodini o'qing yoki ekrandan mahsulotni (masalan: *Hydrolife suv, Flash Up, Protein batoncha*) savatchaga qo'shing.
3. To'lov turini tanlang (Naqd, Karta).
4. **"Savdoni yakunlash"** tugmasini bosing:
   - Ombor qoldig'idan mahsulotlar avtomatik yechiladi.
   - Kassa tushumiga pul qo'shiladi.
   - PDF kassa cheki chiqariladi.
5. Agar xato sotilgan bo'lsa, **"Savdolar tarixi"** bo'limidan mahsulotni qaytarish (refund) tugmasi bosiladi va mahsulot omborga qaytariladi.

---

## 7. XARAJATLAR VA HISOBOTLAR

- **Xarajatlar:** Har qanday sarf-xarajatlar (ijara, elektr energiyasi, suv, xodimlar maoshi, jihozlarni ta'mirlash) **"Xarajatlar"** bo'limiga kiritiladi.
- **Boshqaruv paneli (Dashboard):** Bugungi va oylik sof foyda (`Tushum - Xarajatlar`) real vaqt rejimida avtomatik hisoblab boriladi.
- **Hisobotlar:** **"Hisobotlar"** bo'limidan istalgan sana oralig'idagi moliyaviy va mijozlar hisobotini **Excel (.xlsx)** yoki **PDF** shaklida bir marta bosish bilan yuklab olishingiz mumkin.

---

## 8. XAVFSIZLIK VA MA'LUMOTLAR BAZASINI ZAXIRALASH (BACKUP)

1. **Avtomatik zaxiralash:** Tizim har kuni kechasi soat 23:00 da barcha ma'lumotlarni siqilgan `.sql.gz` fayl shaklida `backups/` papkasiga saqlab boradi.
2. **Qo'lda zaxira olish:** **"Sozlamalar"** bo'limiga o'tib, **"Hozir zaxira nusxa yaratish"** tugmasini bosishingiz kifoya.
3. **Fleshkaga ko'chirish:** Haftada bir marta `backups/` papkasidagi eng so'nggi arxiv faylini alohida tashqi USB fleshkaga nusxalab olish tavsiya etiladi.
