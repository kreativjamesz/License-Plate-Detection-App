-- SQL Script to Update Existing Database for Duplicate Prevention
-- Run this AFTER youhave the license_plate_detection database

USE license_plate_detection;

-- Add new columns for duplicate prevention
ALTER TABLE license_plates 
ADD COLUMN best_confidence DECIMAL(5,2) DEFAULT 0.00 AFTER confidence,
ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER detected_at,
ADD COLUMN detection_count INT DEFAULT 1 AFTER last_seen,
ADD COLUMN first_location VARCHAR(100) DEFAULT 'Camera' AFTER detection_count,
ADD COLUMN latest_location VARCHAR(100) DEFAULT 'Camera' AFTER first_location,
ADD COLUMN best_coordinates JSON NULL AFTER coordinates;

-- Update existing records with new column values
UPDATE license_plates SET 
    best_confidence = confidence,
    detection_count = 1,
    first_location = location,
    latest_location = location,
    best_coordinates = coordinates,
    last_seen = detected_at
WHERE best_confidence IS NULL OR best_confidence = 0;

-- Create additional indexes for better performance
CREATE INDEX idx_plates_last_seen ON license_plates(last_seen);
CREATE INDEX idx_plates_detection_count ON license_plates(detection_count);
CREATE INDEX idx_plates_text_location_time ON license_plates(plate_text, latest_location, last_seen);

-- Show the updated table structure
DESCRIBE license_plates;

-- Update existing plates with dashes to valid format
UPDATE license_plates SET plate_text = '518 UOZ' WHERE plate_text = '518-UOZ';
UPDATE license_plates SET plate_text = '123 ABC' WHERE plate_text = 'ABC-1234';
UPDATE license_plates SET plate_text = '567 XYZ' WHERE plate_text = 'XYZ-5678';
UPDATE license_plates SET plate_text = '901 DEF' WHERE plate_text = 'DEF-9012';
UPDATE license_plates SET plate_text = '345 GHI' WHERE plate_text = 'GHI-3456';
UPDATE license_plates SET plate_text = '789 JKL' WHERE plate_text = 'JKL-7890';
UPDATE license_plates SET plate_text = '246 MNO' WHERE plate_text = 'MNO-2468';
UPDATE license_plates SET plate_text = '135 PQR' WHERE plate_text = 'PQR-1357';
UPDATE license_plates SET plate_text = '975 STU' WHERE plate_text = 'STU-9753';
UPDATE license_plates SET plate_text = '864 VWX' WHERE plate_text = 'VWX-8642';
UPDATE license_plates SET plate_text = '468 YZA' WHERE plate_text = 'YZA-4680';

-- Show sample data with new columns
SELECT id, plate_text, confidence, best_confidence, detection_count, 
       first_location, latest_location, detected_at, last_seen 
FROM license_plates 
LIMIT 5;

SELECT 'Database updated successfully for duplicate prevention!' as result;
