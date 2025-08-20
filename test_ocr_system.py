#!/usr/bin/env python3
"""
Test script for OCR-enabled license plate detection system
"""

import sys
import os
sys.path.append('app')

import cv2
import numpy as np
from app.services.ocr_service import ocr_service, get_ocr_stats, is_ocr_available
from app.services.plate.detector import detect_and_read_license_plates, plate_detector
from app.services.detection_logger import detection_logger
from app.utils.plate_validator import validate_plate

def test_ocr_availability():
    """Test if OCR service is available"""
    print("🔤 Testing OCR Availability...")
    available = is_ocr_available()
    print(f"OCR Available: {'✅ YES' if available else '❌ NO'}")
    
    if available:
        stats = get_ocr_stats()
        print(f"OCR Stats: {stats}")
    
    print()
    return available

def test_camera_detection():
    """Test camera-based detection with OCR"""
    print("📷 Testing Camera Detection with OCR...")
    
    try:
        # Try to open camera
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("❌ Cannot open camera for testing")
            return
        
        print("✅ Camera opened successfully")
        print("📸 Capturing frames for OCR testing...")
        print("💡 Point camera at license plates or press ESC to exit")
        
        frame_count = 0
        successful_reads = 0
        
        while frame_count < 20:  # Test 20 frames
            ret, frame = camera.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Resize for better performance
            frame = cv2.resize(frame, (640, 480))
            
            # Detect and read plates
            plate_results = detect_and_read_license_plates(frame)
            
            # Process results
            display_frame = frame.copy()
            if plate_results:
                display_frame = plate_detector.draw_plates_with_text(display_frame, plate_results)
                
                for i, plate_info in enumerate(plate_results):
                    text = plate_info.get('text')
                    confidence = plate_info.get('confidence', 0.0)
                    valid = plate_info.get('valid', False)
                    
                    if valid and text:
                        successful_reads += 1
                        print(f"📖 Frame {frame_count}: Read '{text}' (confidence: {confidence:.2f})")
                        
                        # Test validation
                        is_valid, normalized, plate_type = validate_plate(text)
                        print(f"   Validation: {'✅ VALID' if is_valid else '❌ INVALID'} | Normalized: '{normalized}' | Type: {plate_type}")
                    else:
                        print(f"🔍 Frame {frame_count}: Plate detected but OCR failed")
            else:
                print(f"🚫 Frame {frame_count}: No plates detected")
            
            # Show frame (optional)
            cv2.imshow('OCR Test - Press ESC to exit', display_frame)
            
            # Check for ESC key
            key = cv2.waitKey(100) & 0xFF
            if key == 27:  # ESC key
                break
        
        camera.release()
        cv2.destroyAllWindows()
        
        # Results
        success_rate = (successful_reads / frame_count * 100) if frame_count > 0 else 0
        print(f"\n📊 Test Results:")
        print(f"   Frames processed: {frame_count}")
        print(f"   Successful OCR reads: {successful_reads}")
        print(f"   Success rate: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Camera test error: {e}")

def test_validation_with_ocr():
    """Test validation system with various plate formats"""
    print("🧪 Testing Validation with OCR...")
    
    # Mock OCR results to test validation
    mock_ocr_results = [
        ("518 UOZ", 0.95, True),
        ("518UOZ", 0.92, True),
        ("ABC 123", 0.89, True),
        ("518-UOZ", 0.91, False),  # Should be rejected
        ("PLATE_123", 0.88, False),  # Should be rejected
        ("123", 0.85, False),  # Too short
        ("", 0.0, False),  # Empty
    ]
    
    for text, confidence, expected_valid in mock_ocr_results:
        is_valid, normalized, plate_type = validate_plate(text)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"{status} | '{text:12}' | Valid: {is_valid:5} | Expected: {expected_valid:5} | Normalized: '{normalized or 'None':8}'")
    
    print()

def test_detection_logger_with_ocr():
    """Test detection logger with OCR results"""
    print("📝 Testing Detection Logger with OCR...")
    
    # Test valid plates
    test_plates = [
        ("518 UOZ", 0.95, (100, 100, 50, 20)),
        ("ABC 123", 0.89, (150, 120, 55, 22)),
        ("518-UOZ", 0.91, (200, 140, 52, 21)),  # Should be rejected
    ]
    
    for plate_text, confidence, coordinates in test_plates:
        logged = detection_logger.log_detection(
            plate_text=plate_text,
            confidence=confidence,
            location="Test Camera",
            coordinates=coordinates
        )
        
        result = "✅ LOGGED" if logged else "❌ REJECTED"
        print(f"{result} | '{plate_text}' (confidence: {confidence:.2f})")
    
    # Check log stats
    today_count = detection_logger.get_today_detections_count()
    print(f"\n📊 Total logged today: {today_count}")
    
    print()

def main():
    """Run all OCR tests"""
    print("🚗 License Plate OCR System Tests")
    print("=" * 50)
    
    try:
        # Test 1: OCR availability
        ocr_available = test_ocr_availability()
        
        # Test 2: Validation system
        test_validation_with_ocr()
        
        # Test 3: Detection logger
        test_detection_logger_with_ocr()
        
        # Test 4: Camera detection (if OCR available)
        if ocr_available:
            response = input("🤔 Test camera detection with OCR? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                test_camera_detection()
        else:
            print("⚠️ Skipping camera test - OCR not available")
        
        print("\n✅ All OCR tests completed!")
        print("\n📋 Summary:")
        print("- OCR service uses EasyOCR for text recognition")
        print("- Only plates matching '### XXX' format are accepted") 
        print("- Plates with dashes, underscores, or invalid formats are rejected")
        print("- Camera detection now shows real license plate text")
        print("- Detection logger only logs plates with valid OCR text")
        
        # Show final OCR stats
        if ocr_available:
            final_stats = get_ocr_stats()
            print(f"\n📈 Final OCR Statistics: {final_stats}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
