# 2D QR-SKANERNI ULASH VA SOZLASH YO'RIQNOMASI

IRON FITNESS CLUB tizimi barcha standart 2D QR va shtrix-kod skanerlari (Netum, Honeywell, Zebra, Eyoyo, Datalogic va barcha xitoylik USB 2D skanerlar) bilan mos ishlaydi.

---

## 1. JISMONIY ULASH (HARDWARE SETUP)

1. Skanerning USB kabelini reception kompyuterining USB portiga ulang.
2. Windows qurilmani **"HID Keyboard Device"** (klaviatura qurilmasi) sifatida taniydi. Hech qanday maxsus drayver talab qilinmaydi.
3. Skaner ulanganligini tekshirish uchun kompyuterda oddiy **Notepad (Bloknot)** dasturini oching va istalgan QR-kod yoki shtrix-kodni skaner qiling:
   - Skaner signali (bip) eshitiladi.
   - Bloknotga kod matni yoziladi va kursor avtomatik yangi qatorga o'tadi (`Enter / CR / LF`).

---

## 2. SKANER PARAMETRLARI (DEFAULT SOZLAMALARI)

Skaneringiz qutisidan chiqqan yo'riqnomadagi quyidagi 2 ta shtrix-kodni o'qitish kifoya:
1. **USB HID Mode** (Klaviatura kiritish rejimi).
2. **Auto Enter / Suffix CR+LF** (O'qigandan so'ng avtomatik `Enter` tugmasini bosish).

---

## 3. ZALGA KIRISHDA QANDAY FOYDALANILADI?

1. Brauzerda **"QR Skaner"** sahifasini oching:  
   `http://127.0.0.1:5000/visits/scanner`
2. Kiritish maydoni (`#barcodeInput`) sahifa ochilishi bilan **avtomatik fokusda** turadi.
3. Mijoz kartasidagi QR-kodni skaner oldiga tutishi bilan:
   - Skaner kodni maydonga kiritadi va avtomatik `Enter` bosadi.
   - Ekran yashil yonadi: Mijozning ismi, tarifi, qolgan kunlari va surati ko'rinadi.
   - Agar xatolik bo'lsa (muddati o'tgan, toq kunda juft kelgan yoki bugun 2-marta kelgan), ekran qizil yonadi va sababi katta harflarda ovozli signal bilan ko'rsatiladi.
4. Reception xodimi har safar sichqonchani bosishi shart emas — tizim avtomatik navbatdagi skanerlashga tayyor turadi.
