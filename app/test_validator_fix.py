#!/usr/bin/env python3
"""Test the improved validator with OCR error correction"""

from utils.plate_validator import validate_plate

def test_ocr_corrections():
    test_plates = [
        'J00 OO4',  # Should become J00 004 (first part numeric)
        '518 UOZ',  # Already valid
        'ABC 123',  # Already valid  
        '5I8 U0Z',  # Should become 518 UOZ
        'AB0 I23',  # Should become AB0 123
        'O12 ABC',  # Should become 012 ABC
        'I23 S56',  # Should become 123 556
    ]
    
    print('🧪 Testing OCR Error Correction:')
    print('Original    | Valid | Normalized | Type')
    print('-' * 45)
    
    for plate in test_plates:
        is_valid, normalized, plate_type = validate_plate(plate)
        status = '✅' if is_valid else '❌'
        print(f'{status} {plate:10} | {str(is_valid):5} | {normalized or "None":10} | {plate_type}')

if __name__ == "__main__":
    test_ocr_corrections()
