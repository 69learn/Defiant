CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_type ENUM('test', '1_month', '3_month') NOT NULL,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_active (user_id, is_active),
    INDEX idx_end_date (end_date)
);

-- Add has_used_trial to users table (ignore if already exists)
ALTER TABLE users ADD COLUMN has_used_trial BOOLEAN DEFAULT FALSE;
