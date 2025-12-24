-- Migration: Create crypto_payments table
-- This table stores cryptocurrency payment transactions

CREATE TABLE IF NOT EXISTS crypto_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    toman_amount DECIMAL(15, 2) NOT NULL,
    crypto_amount DECIMAL(15, 6) NOT NULL,
    wallet_address VARCHAR(100) NOT NULL,
    status ENUM('pending', 'completed', 'expired', 'cancelled') DEFAULT 'pending',
    payment_timestamp BIGINT,
    expires_at TIMESTAMP NOT NULL,
    txid VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_order_number (order_number),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add index for performance
CREATE INDEX idx_pending_payments ON crypto_payments(status, expires_at);
