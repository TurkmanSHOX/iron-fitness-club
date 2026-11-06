-- =====================================================================
-- IRON FITNESS CLUB - BOSHLANG'ICH MA'LUMOTLAR (SEED DATA)
-- HeidiSQL orqali `schema.sql` dan keyin ishga tushiring
-- =====================================================================

USE `iron_fitness_club`;

-- 1. ADMINISTRATOR (Boshlang'ich vaqtinchalik ma'lumotlar; dastlabki kirishda tizim parolni almashtirishni majburiy talab qiladi)
INSERT INTO `admins` (`id`, `username`, `password_hash`, `full_name`, `phone`, `role`, `is_active`, `is_password_changed`)
VALUES (1, 'admin', 'scrypt:32768:8:1$17B2iZ1s6n2K9b8r$e1cf8d1d81aa38914ba1faee12dfb66d43e2a4a7cfcb7ff8910072049d5bfcb1056503c2714a601bb9903e1e44fdbb790d984dfab67fe6cb51b72e5050fbe7ba', 'Bosh Administrator', '+998901234567', 'admin', 1, 0)
ON DUPLICATE KEY UPDATE `full_name` = VALUES(`full_name`);

-- 2. DASTLABKI 4 TA TARIF
INSERT INTO `tariffs` (`id`, `name`, `type`, `duration_days`, `price`, `description`, `is_active`)
VALUES 
(1, '1 kunlik tashrif', 'single', 1, 20000.00, 'Zalga 1 martalik kirish huquqini beruvchi tarif', 1),
(2, '1 oylik - Juft kunlar', 'even_days', 30, 300000.00, 'Faqat oyning juft sanalarida (2, 4, 6, 8, 10...) kirish', 1),
(3, '1 oylik - Toq kunlar', 'odd_days', 30, 300000.00, 'Faqat oyning toq sanalarida (1, 3, 5, 7, 9...) kirish', 1),
(4, '1 oylik - Har kuni', 'daily', 30, 400000.00, 'Oyning barcha kunlarida cheklovsiz kirish imkoniyati', 1)
ON DUPLICATE KEY UPDATE `price` = VALUES(`price`), `description` = VALUES(`description`);

-- 3. TIZIM SOZLAMALARI
INSERT INTO `settings` (`setting_key`, `setting_value`, `description`)
VALUES
('club_name', 'IRON FITNESS CLUB', 'Sport klubining rasmiy nomi'),
('club_phone', '+998 90 123 45 67', 'Reception va klub aloqa telefoni'),
('club_address', 'Urganch shahri, Al-Xorazmiy ko''chasi, 24-uy', 'Klub manzili'),
('currency', 'UZS', 'Asosiy pul birligi'),
('max_freeze_days', '10', 'Bir martada ruxsat berilgan maksimal muzlatish kuni'),
('max_freeze_per_period', '1', 'Bir oylik abonement davrida muzlatishlar soni'),
('single_entry_per_day', 'true', 'Mijoz bir kunda faqat 1 marta kirishiga ruxsat berish'),
('allow_manual_override', 'true', 'Admin istisno tariqasida qo''lda ruxsat bera oladi'),
('notify_before_days', '3,1,0', 'Abonement tugashidan oldin eslatma kunlari')
ON DUPLICATE KEY UPDATE `setting_value` = VALUES(`setting_value`);

-- 4. MAHSULOT KATEGORIYALARI
INSERT INTO `product_categories` (`id`, `name`, `description`, `is_active`)
VALUES
(1, 'Suv va Ichimliklar', 'Mineral suvlar, vitaminli va izotonik ichimliklar', 1),
(2, 'Energetiklar', 'Sport energetik ichimliklari va pre-workoutlar', 1),
(3, 'Sport oziq-ovqatlari', 'Protein, kreatin, geyner va BCAA kabi qo''shimchalar', 1),
(4, 'Protein batonchalari', 'Turli xil sport batonchalari va shirinliklar', 1)
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- 5. YETKAZIB BERUVCHILAR
INSERT INTO `suppliers` (`id`, `name`, `phone`, `address`, `contact_person`, `is_active`)
VALUES
(1, 'Sport Nutrition Tashkent', '+998712001122', 'Toshkent sh., Chilonzor', 'Jahongir aka', 1),
(2, 'Hydro Water MChJ', '+998622241100', 'Urganch sh., Sanoat zonasi', 'Mansur', 1)
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- 6. DASTLABKI MAHSULOTLAR
INSERT INTO `products` (`id`, `category_id`, `supplier_id`, `name`, `barcode`, `purchase_price`, `sale_price`, `stock_quantity`, `unit`, `min_stock_alert`, `expiry_date`, `is_active`)
VALUES
(1, 1, 2, 'Hydrolife Gazsiz Suv 0.5L', '4780001234567', 2500.00, 5000.00, 50, 'dona', 10, '2027-12-31', 1),
(2, 2, 1, 'Flash Up Max Energetik 0.45L', '4600682012345', 7000.00, 12000.00, 30, 'dona', 8, '2027-06-30', 1),
(3, 3, 1, 'Gold Standard Whey 100% 908g', '6901234567890', 280000.00, 390000.00, 10, 'banka', 3, '2028-01-01', 1),
(4, 4, 1, 'Bombbar Protein Batoncha 60g', '4620012345678', 12000.00, 20000.00, 40, 'dona', 10, '2027-09-15', 1),
(5, 3, 1, 'Creatine Monohydrate 300g', '7901234567891', 130000.00, 190000.00, 15, 'banka', 4, '2028-03-31', 1)
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`), `sale_price` = VALUES(`sale_price`);
