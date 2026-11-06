-- =====================================================================
-- IRON FITNESS CLUB - FITNES ZALINI AVTOMATLASHTIRISH TIZIMI
-- BAZA: MariaDB / MySQL (HeidiSQL orqali to'liq import qilinadi)
-- CHARSET: utf8mb4 / COLLATE: utf8mb4_unicode_ci
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `iron_fitness_club` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `iron_fitness_club`;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. ADMINISTRATORLAR
DROP TABLE IF EXISTS `admins`;
CREATE TABLE `admins` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(100) NOT NULL,
    `phone` VARCHAR(20) DEFAULT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'admin',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `last_login` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. MIJOZLAR
DROP TABLE IF EXISTS `clients`;
CREATE TABLE `clients` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(100) NOT NULL,
    `phone` VARCHAR(20) NOT NULL UNIQUE,
    `birth_date` DATE DEFAULT NULL,
    `gender` ENUM('male', 'female', 'other') DEFAULT 'male',
    `photo_url` VARCHAR(255) DEFAULT NULL,
    `qr_code` VARCHAR(64) NOT NULL UNIQUE,
    `status` ENUM('active', 'inactive', 'archived') NOT NULL DEFAULT 'active',
    `notes` TEXT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_client_phone` (`phone`),
    INDEX `idx_client_qr` (`qr_code`),
    INDEX `idx_client_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. TELEGRAM FOYDALANUVCHILARI
DROP TABLE IF EXISTS `telegram_users`;
CREATE TABLE `telegram_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT DEFAULT NULL,
    `telegram_id` BIGINT NOT NULL UNIQUE,
    `username` VARCHAR(100) DEFAULT NULL,
    `first_name` VARCHAR(100) DEFAULT NULL,
    `last_name` VARCHAR(100) DEFAULT NULL,
    `phone_number` VARCHAR(20) DEFAULT NULL,
    `step` VARCHAR(50) DEFAULT 'start',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_tg_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE SET NULL,
    INDEX `idx_tg_id` (`telegram_id`),
    INDEX `idx_tg_phone` (`phone_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. MIJOZ QR-KODLARI (Doimiy va yangilanadigan yagona identifikatorlar)
DROP TABLE IF EXISTS `client_qr_codes`;
CREATE TABLE `client_qr_codes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT NOT NULL,
    `qr_code_token` VARCHAR(64) NOT NULL UNIQUE,
    `qr_image_path` VARCHAR(255) DEFAULT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `generated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_qrcode_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    INDEX `idx_qr_token` (`qr_code_token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. TARIFLAR
DROP TABLE IF EXISTS `tariffs`;
CREATE TABLE `tariffs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `type` ENUM('single', 'even_days', 'odd_days', 'daily') NOT NULL,
    `duration_days` INT NOT NULL DEFAULT 30,
    `price` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `description` TEXT DEFAULT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. SOTILGAN ABONEMENTLAR
DROP TABLE IF EXISTS `subscriptions`;
CREATE TABLE `subscriptions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT NOT NULL,
    `tariff_id` INT NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `original_price` DECIMAL(14, 2) NOT NULL,
    `paid_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `status` ENUM('active', 'expired', 'frozen', 'cancelled') NOT NULL DEFAULT 'active',
    `freeze_count` INT NOT NULL DEFAULT 0,
    `notes` TEXT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sub_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sub_tariff` FOREIGN KEY (`tariff_id`) REFERENCES `tariffs` (`id`) ON DELETE RESTRICT,
    INDEX `idx_sub_dates` (`start_date`, `end_date`),
    INDEX `idx_sub_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. ABONEMENT O'ZGARISHLARI TARIXI
DROP TABLE IF EXISTS `subscription_history`;
CREATE TABLE `subscription_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `subscription_id` INT NOT NULL,
    `action` ENUM('created', 'renewed', 'tariff_changed', 'frozen', 'unfrozen', 'cancelled') NOT NULL,
    `old_status` VARCHAR(20) DEFAULT NULL,
    `new_status` VARCHAR(20) DEFAULT NULL,
    `old_end_date` DATE DEFAULT NULL,
    `new_end_date` DATE DEFAULT NULL,
    `notes` TEXT DEFAULT NULL,
    `created_by` VARCHAR(50) DEFAULT 'system',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_subhist_sub` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. ABONEMENTNI MUZLATISH SO'ROVLARI VA QARORLARI
DROP TABLE IF EXISTS `freeze_requests`;
CREATE TABLE `freeze_requests` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `subscription_id` INT NOT NULL,
    `client_id` INT NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `days_count` INT NOT NULL,
    `reason` TEXT DEFAULT NULL,
    `status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    `admin_comment` TEXT DEFAULT NULL,
    `reviewed_by` INT DEFAULT NULL,
    `reviewed_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_freeze_sub` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_freeze_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_freeze_admin` FOREIGN KEY (`reviewed_by`) REFERENCES `admins` (`id`) ON DELETE SET NULL,
    INDEX `idx_freeze_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. TASHRIFLAR VA KIRISH NAZORATI
DROP TABLE IF EXISTS `visits`;
CREATE TABLE `visits` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT NOT NULL,
    `subscription_id` INT DEFAULT NULL,
    `visit_date` DATE NOT NULL,
    `visit_time` TIME NOT NULL,
    `scan_type` ENUM('qr', 'manual') NOT NULL DEFAULT 'qr',
    `status` ENUM('allowed', 'denied') NOT NULL DEFAULT 'allowed',
    `denial_reason` VARCHAR(255) DEFAULT NULL,
    `notes` VARCHAR(255) DEFAULT NULL,
    `admin_id` INT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_visit_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_visit_sub` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_visit_admin` FOREIGN KEY (`admin_id`) REFERENCES `admins` (`id`) ON DELETE SET NULL,
    INDEX `idx_visit_date` (`visit_date`),
    INDEX `idx_visit_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. KIRISH URINISHLARI (Audit jurnali)
DROP TABLE IF EXISTS `access_attempts`;
CREATE TABLE `access_attempts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT DEFAULT NULL,
    `qr_code` VARCHAR(64) DEFAULT NULL,
    `status` ENUM('allowed', 'denied') NOT NULL,
    `reason` VARCHAR(255) DEFAULT NULL,
    `scanned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_access_qr` (`qr_code`),
    INDEX `idx_access_time` (`scanned_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. AKSIYALAR
DROP TABLE IF EXISTS `promotions`;
CREATE TABLE `promotions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(150) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `discount_type` ENUM('percent', 'fixed') NOT NULL DEFAULT 'percent',
    `discount_value` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `target_tariff_id` INT DEFAULT NULL,
    `target_audience` ENUM('all', 'new') NOT NULL DEFAULT 'all',
    `max_uses` INT DEFAULT NULL,
    `current_uses` INT NOT NULL DEFAULT 0,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_promo_tariff` FOREIGN KEY (`target_tariff_id`) REFERENCES `tariffs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. PROMO-KODLAR
DROP TABLE IF EXISTS `promo_codes`;
CREATE TABLE `promo_codes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `promotion_id` INT NOT NULL,
    `code` VARCHAR(50) NOT NULL UNIQUE,
    `is_used` BOOLEAN NOT NULL DEFAULT FALSE,
    `used_by_client_id` INT DEFAULT NULL,
    `used_at` DATETIME DEFAULT NULL,
    CONSTRAINT `fk_code_promo` FOREIGN KEY (`promotion_id`) REFERENCES `promotions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_code_client` FOREIGN KEY (`used_by_client_id`) REFERENCES `clients` (`id`) ON DELETE SET NULL,
    INDEX `idx_promo_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. MAHSULOT KATEGORIYALARI
DROP TABLE IF EXISTS `product_categories`;
CREATE TABLE `product_categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT DEFAULT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. YETKAZIB BERUVCHILAR
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `phone` VARCHAR(30) DEFAULT NULL,
    `address` VARCHAR(255) DEFAULT NULL,
    `contact_person` VARCHAR(100) DEFAULT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. MAHSULOTLAR
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_id` INT DEFAULT NULL,
    `supplier_id` INT DEFAULT NULL,
    `name` VARCHAR(150) NOT NULL,
    `barcode` VARCHAR(64) NOT NULL UNIQUE,
    `purchase_price` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `sale_price` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `stock_quantity` INT NOT NULL DEFAULT 0,
    `unit` VARCHAR(20) NOT NULL DEFAULT 'dona',
    `min_stock_alert` INT NOT NULL DEFAULT 5,
    `expiry_date` DATE DEFAULT NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_prod_cat` FOREIGN KEY (`category_id`) REFERENCES `product_categories` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_prod_sup` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL,
    INDEX `idx_prod_barcode` (`barcode`),
    INDEX `idx_prod_stock` (`stock_quantity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. OMBOR HARAKATLARI
DROP TABLE IF EXISTS `stock_movements`;
CREATE TABLE `stock_movements` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `product_id` INT NOT NULL,
    `movement_type` ENUM('in', 'out_sale', 'return', 'write_off', 'inventory_adjustment') NOT NULL,
    `quantity` INT NOT NULL,
    `previous_stock` INT NOT NULL,
    `new_stock` INT NOT NULL,
    `unit_price` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `total_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `reference_id` VARCHAR(50) DEFAULT NULL,
    `notes` TEXT DEFAULT NULL,
    `created_by` VARCHAR(50) DEFAULT 'admin',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_stock_prod` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT,
    INDEX `idx_stock_prod` (`product_id`),
    INDEX `idx_stock_type` (`movement_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 17. SAVDO OPERATSIYALARI (POS)
DROP TABLE IF EXISTS `sales`;
CREATE TABLE `sales` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sale_number` VARCHAR(50) NOT NULL UNIQUE,
    `client_id` INT DEFAULT NULL,
    `total_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `discount_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `final_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `cost_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `gross_profit` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `payment_method` ENUM('cash', 'card', 'click', 'payme') NOT NULL DEFAULT 'cash',
    `status` ENUM('completed', 'cancelled', 'refunded') NOT NULL DEFAULT 'completed',
    `receipt_pdf_path` VARCHAR(255) DEFAULT NULL,
    `notes` TEXT DEFAULT NULL,
    `created_by` VARCHAR(50) DEFAULT 'admin',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sale_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE SET NULL,
    INDEX `idx_sale_num` (`sale_number`),
    INDEX `idx_sale_date` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 18. SAVDO TARKIBIDAGI MAHSULOTLAR
DROP TABLE IF EXISTS `sale_items`;
CREATE TABLE `sale_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sale_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `product_name` VARCHAR(150) NOT NULL,
    `barcode` VARCHAR(64) DEFAULT NULL,
    `purchase_price` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `unit_price` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `quantity` INT NOT NULL DEFAULT 1,
    `total_price` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_saleitem_sale` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_saleitem_prod` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 19. TO'LOVLAR
DROP TABLE IF EXISTS `payments`;
CREATE TABLE `payments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `payment_number` VARCHAR(50) NOT NULL UNIQUE,
    `client_id` INT NOT NULL,
    `subscription_id` INT DEFAULT NULL,
    `sale_id` INT DEFAULT NULL,
    `payment_type` ENUM('subscription', 'single_visit', 'product_sale', 'other') NOT NULL,
    `amount` DECIMAL(14, 2) NOT NULL,
    `payment_method` ENUM('cash', 'card', 'click', 'payme') NOT NULL,
    `status` ENUM('pending', 'completed', 'failed', 'refunded') NOT NULL DEFAULT 'completed',
    `transaction_id` VARCHAR(100) DEFAULT NULL,
    `receipt_pdf_path` VARCHAR(255) DEFAULT NULL,
    `created_by` VARCHAR(50) DEFAULT 'admin',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_pay_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_pay_sub` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_pay_sale` FOREIGN KEY (`sale_id`) REFERENCES `sales` (`id`) ON DELETE SET NULL,
    INDEX `idx_pay_num` (`payment_number`),
    INDEX `idx_pay_date` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 20. TO'LOV TRANZAKSIYALARI (Click, Payme webhook loglari)
DROP TABLE IF EXISTS `payment_transactions`;
CREATE TABLE `payment_transactions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `payment_id` INT DEFAULT NULL,
    `provider` ENUM('click', 'payme') NOT NULL,
    `provider_transaction_id` VARCHAR(100) NOT NULL,
    `request_payload` LONGTEXT DEFAULT NULL,
    `response_payload` LONGTEXT DEFAULT NULL,
    `status` VARCHAR(50) NOT NULL,
    `error_message` VARCHAR(255) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_paytrans_pay` FOREIGN KEY (`payment_id`) REFERENCES `payments` (`id`) ON DELETE SET NULL,
    INDEX `idx_provider_tx` (`provider`, `provider_transaction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 21. XARAJATLAR
DROP TABLE IF EXISTS `expenses`;
CREATE TABLE `expenses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category` ENUM('rent', 'electricity', 'water', 'salary', 'inventory_purchase', 'repair', 'other') NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `amount` DECIMAL(14, 2) NOT NULL,
    `payment_method` ENUM('cash', 'card', 'bank_transfer') NOT NULL DEFAULT 'cash',
    `expense_date` DATE NOT NULL,
    `receipt_image` VARCHAR(255) DEFAULT NULL,
    `notes` TEXT DEFAULT NULL,
    `created_by` VARCHAR(50) DEFAULT 'admin',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_expense_date` (`expense_date`),
    INDEX `idx_expense_cat` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 22. BILDIRISHNOMALAR (Telegram orqali yuboriladigan)
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `client_id` INT DEFAULT NULL,
    `telegram_id` BIGINT NOT NULL,
    `message_type` ENUM('sub_expiring_3days', 'sub_expiring_1day', 'sub_expired', 'payment_success', 'freeze_update', 'promo', 'receipt') NOT NULL,
    `message_text` TEXT NOT NULL,
    `status` ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
    `sent_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_notif_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    INDEX `idx_notif_tg` (`telegram_id`),
    INDEX `idx_notif_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 23. SOZLAMALAR
DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `setting_key` VARCHAR(50) NOT NULL UNIQUE,
    `setting_value` TEXT NOT NULL,
    `description` VARCHAR(255) DEFAULT NULL,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 24. AUDIT VA XAVFSIZLIK JURNALI
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `admin_id` INT DEFAULT NULL,
    `action` VARCHAR(100) NOT NULL,
    `target_table` VARCHAR(50) DEFAULT NULL,
    `target_id` INT DEFAULT NULL,
    `details` TEXT DEFAULT NULL,
    `ip_address` VARCHAR(50) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_audit_time` (`created_at`),
    INDEX `idx_audit_action` (`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 25. ZAXIRALASH TARIXI
DROP TABLE IF EXISTS `backup_logs`;
CREATE TABLE `backup_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `file_name` VARCHAR(255) NOT NULL,
    `file_size` BIGINT NOT NULL DEFAULT 0,
    `backup_type` ENUM('auto', 'manual') NOT NULL DEFAULT 'auto',
    `status` ENUM('success', 'failed') NOT NULL DEFAULT 'success',
    `message` TEXT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
