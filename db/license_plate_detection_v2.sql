-- License Plate Detection Database - Version 2 with Duplicate Prevention
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

-- License Plates Table with Duplicate Prevention
CREATE TABLE license_plates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_text VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,2) DEFAULT 0.00,
    best_confidence DECIMAL(5,2) DEFAULT 0.00, -- Track highest confidence ever detected
    location VARCHAR(100) DEFAULT 'Camera',
    coordinates JSON NULL, -- Store latest detection coordinates {x, y, w, h}
    best_coordinates JSON NULL, -- Store coordinates from best confidence detection
    image_path VARCHAR(255) NULL,
    status ENUM('detected','verified','flagged') DEFAULT 'detected',
    notes TEXT NULL,
    flag_reason VARCHAR(255) NULL,
    verified_at TIMESTAMP NULL,
    flagged_at TIMESTAMP NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- First detection time
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- Latest detection time
    detection_count INT DEFAULT 1, -- How many times this plate was detected
    first_location VARCHAR(100) DEFAULT 'Camera', -- Where first detected
    latest_location VARCHAR(100) DEFAULT 'Camera', -- Where last detected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Detection Sessions Table
CREATE TABLE detection_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_name VARCHAR(100) NULL,
    user_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    total_detections INT DEFAULT 0,
    unique_plates INT DEFAULT 0, -- Count of unique plates in session
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

-- Insert sample license plate detections with duplicate prevention data (valid format only)
INSERT INTO license_plates (
    plate_text, confidence, best_confidence, location, coordinates, best_coordinates, 
    status, detection_count, first_location, latest_location, last_seen
) VALUES
('518 UOZ', 0.98, 0.98, 'Test Camera', '{"x": 145, "y": 190, "w": 125, "h": 42}', '{"x": 145, "y": 190, "w": 125, "h": 42}', 'verified', 1, 'Test Camera', 'Test Camera', NOW()),
('123 ABC', 0.95, 0.97, 'Main Camera', '{"x": 150, "y": 200, "w": 120, "h": 40}', '{"x": 148, "y": 198, "w": 122, "h": 42}', 'verified', 5, 'Main Camera', 'Main Camera', NOW() - INTERVAL 5 MINUTE),
('567 XYZ', 0.87, 0.91, 'Main Camera', '{"x": 180, "y": 250, "w": 115, "h": 38}', '{"x": 178, "y": 248, "w": 117, "h": 40}', 'detected', 3, 'Main Camera', 'Side Camera', NOW() - INTERVAL 15 MINUTE),
('901 DEF', 0.92, 0.94, 'Main Camera', '{"x": 200, "y": 180, "w": 125, "h": 42}', '{"x": 198, "y": 182, "w": 127, "h": 44}', 'detected', 2, 'Main Camera', 'Main Camera', NOW() - INTERVAL 8 MINUTE),
('345 GHI', 0.78, 0.82, 'Main Camera', '{"x": 160, "y": 220, "w": 118, "h": 39}', '{"x": 162, "y": 218, "w": 120, "h": 41}', 'flagged', 4, 'Main Camera', 'Side Camera', NOW() - INTERVAL 12 MINUTE),
('789 JKL', 0.89, 0.93, 'Main Camera', '{"x": 170, "y": 210, "w": 122, "h": 41}', '{"x": 168, "y": 208, "w": 124, "h": 43}', 'detected', 7, 'Main Camera', 'Main Camera', NOW() - INTERVAL 3 MINUTE),
('246 MNO', 0.85, 0.88, 'Side Camera', '{"x": 190, "y": 240, "w": 119, "h": 37}', '{"x": 192, "y": 238, "w": 121, "h": 39}', 'detected', 2, 'Side Camera', 'Side Camera', NOW() - INTERVAL 20 MINUTE),
('135 PQR', 0.91, 0.95, 'Main Camera', '{"x": 175, "y": 195, "w": 123, "h": 40}', '{"x": 173, "y": 193, "w": 125, "h": 42}', 'verified', 3, 'Main Camera', 'Main Camera', NOW() - INTERVAL 7 MINUTE),
('975 STU', 0.83, 0.86, 'Side Camera', '{"x": 165, "y": 225, "w": 116, "h": 38}', '{"x": 167, "y": 223, "w": 118, "h": 40}', 'detected', 1, 'Side Camera', 'Side Camera', NOW() - INTERVAL 25 MINUTE),
('864 VWX', 0.88, 0.91, 'Main Camera', '{"x": 185, "y": 205, "w": 121, "h": 39}', '{"x": 183, "y": 203, "w": 123, "h": 41}', 'detected', 1, 'Main Camera', 'Main Camera', NOW() - INTERVAL 30 MINUTE);

-- Create indexes for better performance and duplicate prevention
CREATE INDEX idx_plates_detected_at ON license_plates(detected_at);
CREATE INDEX idx_plates_last_seen ON license_plates(last_seen);
CREATE INDEX idx_plates_status ON license_plates(status);
CREATE INDEX idx_plates_plate_text ON license_plates(plate_text);
CREATE INDEX idx_plates_location ON license_plates(location);
CREATE INDEX idx_plates_detection_count ON license_plates(detection_count);

-- Create composite index for efficient duplicate checking
CREATE INDEX idx_plates_text_location_time ON license_plates(plate_text, latest_location, last_seen);

-- Optional: Create unique constraint to prevent exact duplicates within same location
-- (Comment out if you want to allow same plate in different locations)
-- CREATE UNIQUE INDEX idx_unique_plate_per_location ON license_plates(plate_text, latest_location);

SHOW TABLES;
