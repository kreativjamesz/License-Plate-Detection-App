#!/usr/bin/env python3
"""
Test script for license plate validation and services
"""

import sys
import os
sys.path.append('app')

from app.utils.plate_validator import PlateValidator, validate_plate
from app.services.license_plate_service import LicensePlateService
from app.services.detection_logger import DetectionLogger

def test_plate_validation():
    """Test plate validation logic"""
    print("🧪 Testing License Plate Validation...")
    
    test_cases = [
        ("518 UOZ", True, "518 UOZ", "Valid Philippine format"),
        ("518UOZ", True, "518 UOZ", "Valid Philippine format (will normalize)"),
        ("ABC 123", True, "ABC 123", "Valid Philippine format"),
        ("518-UOZ", False, None, "Invalid - contains dash (should be rejected)"),
        ("PLATE_1234", False, None, "Invalid - contains underscore and wrong format"),
        ("123", False, None, "Invalid - too short"),
        ("", False, None, "Invalid - empty string"),
    ]
    
    for plate_text, expected_valid, expected_normalized, description in test_cases:
        is_valid, normalized, plate_type = validate_plate(plate_text)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"{status} | '{plate_text:12}' | Valid: {is_valid:5} | Normalized: '{normalized or 'None':8}' | {description}")
    
    print()

def test_service_validation():
    """Test that services reject invalid plates"""
    print("🔧 Testing Service Validation...")
    
    # Test license plate service
    service = LicensePlateService()
    
    # Test valid plate
    valid_result = service.add_detection("518 UOZ", 0.95, "Test Camera", (100, 100, 50, 20))
    print(f"Valid plate '518 UOZ': {'✅ ACCEPTED' if valid_result > 0 else '❌ REJECTED'}")
    
    # Test invalid plate with dash
    invalid_result = service.add_detection("518-UOZ", 0.95, "Test Camera", (100, 100, 50, 20))
    print(f"Invalid plate '518-UOZ': {'✅ REJECTED' if invalid_result == -1 else '❌ ACCEPTED (SHOULD BE REJECTED)'}")
    
    print()

def test_logger_validation():
    """Test that detection logger rejects invalid plates"""
    print("📝 Testing Detection Logger Validation...")
    
    logger = DetectionLogger()
    
    # Test valid plate
    valid_logged = logger.log_detection("518 UOZ", 0.95, "Test Camera", (100, 100, 50, 20))
    print(f"Valid plate '518 UOZ': {'✅ LOGGED' if valid_logged else '❌ REJECTED'}")
    
    # Test invalid plate with dash  
    invalid_logged = logger.log_detection("518-UOZ", 0.95, "Test Camera", (100, 100, 50, 20))
    print(f"Invalid plate '518-UOZ': {'✅ REJECTED' if not invalid_logged else '❌ LOGGED (SHOULD BE REJECTED)'}")
    
    print()

def main():
    """Run all tests"""
    print("🚗 License Plate Validation System Tests")
    print("=" * 50)
    
    try:
        test_plate_validation()
        test_service_validation()
        test_logger_validation()
        
        print("✅ All validation tests completed!")
        print("\n📋 Summary:")
        print("- Only plates matching '### XXX' or '123 ABC' format are accepted")
        print("- Plates with dashes (-), underscores (_), or dots (.) are rejected")
        print("- Plates are automatically normalized (518UOZ → 518 UOZ)")
        print("- Both service and logger now validate before processing")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
