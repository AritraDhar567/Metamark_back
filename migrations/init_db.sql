CREATE DATABASE IF NOT EXISTS packaging_compliance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE packaging_compliance;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(255) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title VARCHAR(500),
    listed_price DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'INR',
    seller VARCHAR(255),
    category VARCHAR(100),
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_product_id (product_id),
    INDEX idx_crawled_at (crawled_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Images table
CREATE TABLE IF NOT EXISTS images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    image_url TEXT,
    storage_path TEXT,
    image_type ENUM('main', 'label_front', 'label_back', 'nutrition') DEFAULT 'main',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- OCR Results table
CREATE TABLE IF NOT EXISTS ocr_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_id INT NOT NULL,
    crop_type VARCHAR(50),
    ocr_text TEXT,
    extracted_data JSON,
    confidence DECIMAL(5, 2),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    INDEX idx_image_id (image_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Validation Results table
CREATE TABLE IF NOT EXISTS validations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    ocr_id INT,
    rule_id VARCHAR(50) NOT NULL,
    rule_description TEXT,
    passed BOOLEAN NOT NULL,
    violation_details TEXT,
    severity ENUM('critical', 'major', 'minor') DEFAULT 'major',
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (ocr_id) REFERENCES ocr_results(id) ON DELETE SET NULL,
    INDEX idx_product_id (product_id),
    INDEX idx_passed (passed),
    INDEX idx_rule_id (rule_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Rules table
CREATE TABLE IF NOT EXISTS rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    severity ENUM('critical', 'major', 'minor') DEFAULT 'major',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rule_id (rule_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default rules
INSERT INTO rules (rule_id, rule_name, description, category, severity) VALUES
('R1', 'MRP Presence', 'Maximum Retail Price must be printed on packaging', 'Pricing', 'critical'),
('R2', 'MRP Validity', 'MRP must include currency symbol and be >= 0', 'Pricing', 'critical'),
('R3', 'Net Quantity Standard', 'Net quantity must be in standard units (g, kg, ml, l, nos)', 'Measurement', 'major'),
('R4', 'Net Quantity Presence', 'Net quantity must be declared', 'Measurement', 'critical'),
('R5', 'Manufacturer Name', 'Manufacturer or packer name and address required', 'Identity', 'critical'),
('R6', 'Country of Origin', 'Country of origin must be declared for imported goods', 'Origin', 'major'),
('R7', 'Date Format', 'Manufacturing/Expiry date must be in valid format', 'Dating', 'major'),
('R8', 'Consumer Care Details', 'Consumer care contact details required', 'Support', 'minor'),
('R9', 'FSSAI License', 'FSSAI license number required for food products', 'License', 'critical'),
('R10', 'Nutritional Info', 'Nutritional information required for packaged foods', 'Nutrition', 'major');

-- Processing Queue table
CREATE TABLE IF NOT EXISTS processing_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
