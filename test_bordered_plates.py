#!/usr/bin/env python3
"""
Test script for detecting rectangular bordered license plates
Like the CNN101 and NNN101 plates in the user's image
"""

import sys
import os
sys.path.append('app')

import cv2
import numpy as np
from app.services.plate.detector import plate_detector, detect_and_read_license_plates
from app.services.ocr_service import ocr_service
from app.utils.plate_validator import validate_plate

def test_camera_for_bordered_plates():
    """Test camera detection specifically for bordered plates"""
    print("🔍 Testing Camera Detection for Rectangular Bordered Plates")
    print("=" * 60)
    print("📋 Looking for plates like: CNN101, NNN101 (with character borders)")
    print("💡 Hold Philippine license plates with rectangular character borders in front of camera")
    print("⏹️ Press 'q' to quit, 's' to save current frame")
    print()
    
    try:
        # Open camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return
        
        detection_count = 0
        successful_reads = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize for display
            display_frame = cv2.resize(frame, (800, 600))
            
            # Detect plates with enhanced detection
            plate_results = detect_and_read_license_plates(display_frame)
            
            # Draw results
            result_frame = display_frame.copy()
            
            if plate_results:
                detection_count += 1
                result_frame = plate_detector.draw_plates_with_text(result_frame, plate_results)
                
                # Process each detection
                for i, plate_info in enumerate(plate_results):
                    text = plate_info.get('text')
                    confidence = plate_info.get('confidence', 0.0)
                    valid = plate_info.get('valid', False)
                    coords = plate_info['coordinates']
                    
                    print(f"🔍 Detection #{detection_count}")
                    print(f"   📍 Location: {coords}")
                    print(f"   📝 OCR Text: '{text or 'None'}'")
                    print(f"   🎯 Confidence: {confidence:.3f}")
                    print(f"   ✅ Valid: {valid}")
                    
                    if text and valid:
                        successful_reads += 1
                        is_valid, normalized, plate_type = validate_plate(text)
                        print(f"   🔄 Normalized: '{normalized}'")
                        print(f"   📊 Type: {plate_type}")
                        print(f"   🎉 SUCCESS! Plate recognized and validated")
                    else:
                        print(f"   ⚠️ Needs improvement - OCR failed or invalid format")
                    print()
            
            # Add status overlay
            cv2.putText(result_frame, f"Detections: {detection_count} | Successful: {successful_reads}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(result_frame, "Hold bordered plates (CNN101, NNN101 style) in front of camera", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(result_frame, "Press 'q' to quit, 's' to save frame", 
                       (10, result_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Show frame
            cv2.imshow('Bordered Plate Detection Test', result_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save current frame
                filename = f'test_frame_{detection_count}.jpg'
                cv2.imwrite(filename, display_frame)
                print(f"💾 Saved frame as {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Final summary
        print("\n📊 Test Summary:")
        print(f"   Total detections: {detection_count}")
        print(f"   Successful reads: {successful_reads}")
        if detection_count > 0:
            success_rate = (successful_reads / detection_count) * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        # OCR statistics
        ocr_stats = ocr_service.get_statistics()
        print(f"\n🔤 OCR Statistics:")
        for key, value in ocr_stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

def test_sample_detection():
    """Test detection parameters with synthetic samples"""
    print("🧪 Testing Detection Parameters for Bordered Plates")
    print("=" * 50)
    
    # Test expected plate characteristics
    test_cases = [
        {"text": "CNN101", "expected": True, "format": "CCC###"},
        {"text": "NNN101", "expected": True, "format": "CCC###"},
        {"text": "ABC123", "expected": True, "format": "CCC###"},
        {"text": "123ABC", "expected": True, "format": "###CCC"},
        {"text": "XYZ999", "expected": True, "format": "CCC###"},
    ]
    
    print("Testing validation for bordered plate formats:")
    for case in test_cases:
        text = case["text"]
        expected = case["expected"]
        plate_format = case["format"]
        
        is_valid, normalized, plate_type = validate_plate(text)
        status = "✅ PASS" if is_valid == expected else "❌ FAIL"
        print(f"{status} | {text:8} | Format: {plate_format} | Valid: {is_valid:5} | Normalized: '{normalized or 'None':8}' | Type: {plate_type}")

def main():
    """Run bordered plate detection tests"""
    print("🚗 Rectangular Bordered License Plate Detection Test")
    print("🇵🇭 Optimized for Philippine plates with character borders")
    print()
    
    # Test validation first
    test_sample_detection()
    print()
    
    # Ask user if they want to test camera
    response = input("🎥 Test with camera? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        test_camera_for_bordered_plates()
    else:
        print("📝 Camera test skipped. Run again with 'y' to test camera detection.")

if __name__ == "__main__":
    main()
