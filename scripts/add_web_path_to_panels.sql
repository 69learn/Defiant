-- Migration script to add web_path column to panels table
-- This fixes the "Unknown column 'web_path'" error

USE telegram_bot;

-- Using MySQL-compatible syntax to conditionally add column
SET @dbname = DATABASE();
SET @tablename = "panels";
SET @columnname = "web_path";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  "SELECT 1",
  CONCAT("ALTER TABLE ", @tablename, " ADD COLUMN ", @columnname, " VARCHAR(255) AFTER password")
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Display current table structure
DESCRIBE panels;
