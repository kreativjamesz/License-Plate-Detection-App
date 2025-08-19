-- License Plate Detection Database
-- Updated database schema for license plate detection app

DROP DATABASE IF EXISTS license_plate_detection;
CREATE DATABASE license_plate_detection;
USE license_plate_detection;

-- Users Table (keep existing structure)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','operator','viewer') NOT NULL DEFAULT 'operator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- License Plates Table
CREATE TABLE license_plates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_text VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,2) DEFAULT 0.00,
    location VARCHAR(100) DEFAULT 'Camera',
    coordinates JSON NULL, -- Store detection coordinates {x, y, w, h}
    image_path VARCHAR(255) NULL,
    status ENUM('detected','verified','flagged') DEFAULT 'detected',
    notes TEXT NULL,
    flag_reason VARCHAR(255) NULL,
    verified_at TIMESTAMP NULL,
    flagged_at TIMESTAMP NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Detection Sessions Table (optional - for tracking detection sessions)
CREATE TABLE detection_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_name VARCHAR(100) NULL,
    user_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    total_detections INT DEFAULT 0,
    status ENUM('active','completed','cancelled') DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Logs Table (for tracking actions)
CREATE TABLE logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action TEXT NOT NULL,
    details JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert sample users
INSERT INTO users (username, password, role) VALUES
('admin', 'admin123', 'admin'),
('operator1', 'operator123', 'operator'),
('viewer1', 'viewer123', 'viewer');

-- Insert sample license plate detections
INSERT INTO license_plates (plate_text, confidence, location, coordinates, status) VALUES
('518-UOZ', 0.98, 'Test Camera', '{"x": 145, "y": 190, "w": 125, "h": 42}', 'verified'),
('518UOZ', 0.98, 'Test Camera', '{"x": 145, "y": 190, "w": 125, "h": 42}', 'verified'),
('ABC-1234', 0.95, 'Main Camera', '{"x": 150, "y": 200, "w": 120, "h": 40}', 'verified'),
('XYZ-5678', 0.87, 'Main Camera', '{"x": 180, "y": 250, "w": 115, "h": 38}', 'detected'),
('DEF-9012', 0.92, 'Main Camera', '{"x": 200, "y": 180, "w": 125, "h": 42}', 'detected'),
('GHI-3456', 0.78, 'Main Camera', '{"x": 160, "y": 220, "w": 118, "h": 39}', 'flagged'),
('JKL-7890', 0.89, 'Main Camera', '{"x": 170, "y": 210, "w": 122, "h": 41}', 'detected'),
('MNO-2468', 0.85, 'Side Camera', '{"x": 190, "y": 240, "w": 119, "h": 37}', 'detected'),
('PQR-1357', 0.91, 'Main Camera', '{"x": 175, "y": 195, "w": 123, "h": 40}', 'verified'),
('STU-9753', 0.83, 'Side Camera', '{"x": 165, "y": 225, "w": 116, "h": 38}', 'detected'),
('VWX-8642', 0.88, 'Main Camera', '{"x": 185, "y": 205, "w": 121, "h": 39}', 'detected'),
('YZA-4680', 0.76, 'Main Camera', '{"x": 155, "y": 215, "w": 117, "h": 41}', 'flagged');

-- Create indexes for better performance
CREATE INDEX idx_plates_detected_at ON license_plates(detected_at);
CREATE INDEX idx_plates_status ON license_plates(status);
CREATE INDEX idx_plates_plate_text ON license_plates(plate_text);
CREATE INDEX idx_plates_location ON license_plates(location);

SHOW TABLES;
