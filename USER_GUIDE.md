# IRON FITNESS CLUB — ADMINISTRATOR FOYDALANISH QO‘LLANMASI

Ushbu qo‘llanma **IRON FITNESS CLUB** fitnes zalini avtomatlashtirish tizimidan kundalik foydalanish tartibini tushuntiradi.

---

## 1. Tizimga kirish

1. Brauzerda tizim manzilini oching: `http://127.0.0.1:5000` (yoki server domeni).
2. Dastlabki kirish ma’lumotlari:
   - **Login:** `admin`
   - **Parol:** `admin123`
3. Tizimga birinchi marta kirgandan so‘ng, yuqori o‘ng burchakdagi profil menyusidan **«Parolni o'zgartirish»** bo‘limiga o‘tib, parolingizni o‘zingiz biladigan xavfsiz parolga yangilang.

---

## 2. 2D Skaner orqali kirish nazorati (Reception)

Reception kompyuterida doimiy ravishda **«2D Skaner (Kirish)»** sahifasi ochiq turishi tavsiya etiladi.

1. Sahifa ochilganda skanerlash maydoni **avtomatik fokusda** turadi.
2. Mijoz o‘zining Telegram botidagi yoki chop etilgan kartadagi **QR-kodini** 2D skanerga ko‘rsatadi.
3. Skaner kodni o‘qiganda:
   - **Yashil belgi va yoqimli ovoz:** Mijoz tarifi bugungi kunga mos, to‘langan, muddati faol va bugun birinchi marta kirmoqda $\rightarrow$ **Kirishga ruxsat berildi**.
   - **Qizil belgi va ogohlantiruvchi ovoz:** Kirish rad etildi. Ekrandagi qizil panelda rad etish sababi ko‘rsatiladi (masalan: *«Abonement muddati tugagan»*, *«Muzlatilgan»*, yoki *«Bugun toq sana, sizning tarifingiz: Juft kunlar»*).
4. **Istisno tariqasida ruxsat berish (Admin Override):**
   - Agar mijozning uzrli sababi bo‘lsa (masalan: telefoni o‘chib qolgan), ekranda ochilgan sariq maydonga sababni yozib, **«Istisno tariqasida kiritish»** tugmasini bosing. Bu amal xavfsizlik audit jurnaliga qayd etiladi.

---

## 3. Yangi mijozni ro‘yxatga olish

1. Chap menyudan **«Mijozlar bazasi»** $\rightarrow$ **«Yangi mijoz qo'shish»** tugmasini bosing.
2. F.I.Sh., telefon raqami, jinsi va tug‘ilgan sanasini kiriting.
3. **«Saqlash»** tugmasi bosilganda:
   - Tizim avtomatik ravishda mijoz uchun takrorlanmas shaxsiy **QR-kod** generatsiya qiladi.
   - Mijoz profilida uning QR-kodini yuklab olish va printerdan chiqarib berish mumkin.

---

## 4. Abonement sotish va uzaytirish

1. Mijoz kartochkasidagi yoki menyudagi **«Abonement sotish»** tugmasiga kiring.
2. Mijozni va tarifni tanlang:
   - *1 kunlik tashrif* — 20 000 so‘m
   - *1 oylik (Juft kunlar)* — 300 000 so‘m
   - *1 oylik (Toq kunlar)* — 300 000 so‘m
   - *1 oylik (Har kuni)* — 400 000 so‘m
3. To‘lov usulini belgilang (*Naqd pul*, *Bank kartasi*, *Click*, *Payme*).
4. **«Sotishni tasdiqlash»** tugmasini bosing.
5. Tizim avtomatik ravishda PDF elektron kassa chekini shakllantiradi va mijoz hisobiga to‘lovni qayd etadi.

---

## 5. Abonementni muzlatish so‘rovlarini ko‘rib chiqish

Mijoz Telegram bot orqali muzlatish so‘rovi yuborganda:
1. Chap menyudagi **«Muzlatish so'rovlari»** yonida sariq raqamli bildirishnoma chiqadi.
2. Ushbu bo‘limga kiring: mijozning ismi, so‘ralgan kunlar soni va sababi ko‘rinadi.
3. **«Tasdiqlash»** tugmasi bosilsa:
   - Abonement muddati avtomatik ravishda muzlatilgan kunlar soniga uzaytiriladi!
   - Mijozga Telegram orqali tasdiqlanganlik xabari boradi.
   - Muzlatish davrida mijoz zalga kira olmaydi.
   - Muddat tugagach tizim avtomatik ravishda abonementni yana faol holatga qaytaradi.
4. **«Rad etish»** tugmasi bosilsa, sabab kiritilib so‘rov bekor qilinadi.

---

## 6. Kassa & Bar (POS) savdosi

1. Chap menyudan **«Kassa & Bar (POS)»** oynasini oching.
2. Receptiondagi 2D skanerni ichimlik yoki batonchik ustidagi shtrix-kodga qarating. Mahsulot avtomatik ravishda savatga tushadi.
3. Qo‘lda qo‘shish uchun ekran ustidagi kategoriyalardan birini tanlab, mahsulot ustiga bosing.
4. Miqdorini `+` yoki `-` tugmalari bilan to‘g‘rilang.
5. To‘lov turini tanlang (*Naqd*, *Karta*, *Click*, *Payme*) va **«Savdoni yakunlash»** tugmasini bosing.
6. Ombor qoldig‘i soniyaning ulushlarida real-vaqtda kamayadi va elektron PDF chek ochiladi.
7. Agar mijoz tovarini qaytarsa, **«Savdolar tarixi»** bo‘limiga o‘tib, bir tugma bilan savdoni qaytaring — tovar omborga avtomatik qaytariladi.

---

## 7. Ombor hisobi va Harakatlar

1. **«Ombor & Mahsulotlar»** bo‘limida tovarlar tannarxi, sotuv narxi va qoldiqlari aks etadi.
2. Yangi partiya tovar keltirilganda **«Omborga kirim»** tugmasi orqali qoldiqni oshiring.
3. Yaroqlilik muddati o‘tgan mahsulotlar uchun **«Hisobdan chiqarish (Spisanie)»** funksiyasi mavjud.
4. Har bir amal **«Ombor harakatlari jurnali»**da saqlanib boradi.

---

## 8. Moliya, Xarajatlar va Excel Hisobotlar

1. **«Xarajatlar hisobi»:** Ijara, elektr energiyasi, suv, ish haqi va xo‘jalik xarajatlarini chek rasmi bilan birga tizimga kiriting.
2. **«Hisobotlar & Tahlil»:**
   - Istalgan sana oralig‘ini belgilang.
   - Umumiy tushum, xarajatlar va **sof foyda** hisobini ko‘ring.
   - **«Excel hisobotni yuklab olish»** tugmasini bosib, barcha ko‘rsatkichlarni tayyor `.xlsx` formatida yuklab oling.
