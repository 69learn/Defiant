-- Create access permissions table for granular control
CREATE TABLE IF NOT EXISTS access_permissions (
    permission_id INT AUTO_INCREMENT PRIMARY KEY,
    access_id INT NOT NULL,
    resource_type ENUM('tunnel', 'panel') NOT NULL,
    resource_id INT NOT NULL,
    can_access BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (access_id) REFERENCES shared_access(access_id) ON DELETE CASCADE,
    UNIQUE KEY unique_permission (access_id, resource_type, resource_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
