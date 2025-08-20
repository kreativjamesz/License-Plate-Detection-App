"""
Simple License Plate Validation with OCR Error Correction
Validates Philippine license plate formats with OCR error tolerance
"""

import re
from typing import Optional

class PlateValidator:
    """License plate validator with OCR error tolerance"""
    
    @classmethod
    def validate_and_normalize(cls, plate_text: str) -> tuple[bool, Optional[str], str]:
        """
        Complete validation and normalization with OCR error correction
        Returns: (is_valid, normalized_text, plate_type)
        """
        if not plate_text or not isinstance(plate_text, str):
            return False, None, "invalid"
        
        # Clean input
        clean_text = plate_text.strip().upper()
        
        # Basic length check
        if len(clean_text) < 6 or len(clean_text) > 7:
            return False, None, "invalid"
        
        # Try multiple correction strategies
        candidates = [
            clean_text,  # Original
            cls._fix_spacing(clean_text),  # Fix spacing
            cls._fix_ocr_errors(clean_text),  # Fix OCR errors
            cls._fix_ocr_errors(cls._fix_spacing(clean_text))  # Both
        ]
        
        for candidate in candidates:
            if cls._is_valid_format(candidate):
                return True, candidate, cls._get_plate_type(candidate)
        
        return False, None, "invalid"
    
    @classmethod
    def _fix_spacing(cls, text: str) -> str:
        """Add space if missing"""
        if ' ' in text or len(text) != 6:
            return text
        
        # Try ### XXX format
        return f"{text[:3]} {text[3:]}"
    
    @classmethod
    def _fix_ocr_errors(cls, text: str) -> str:
        """Fix common OCR errors"""
        if ' ' not in text:
            return text
        
        parts = text.split(' ')
        if len(parts) != 2 or len(parts[0]) != 3 or len(parts[1]) != 3:
            return text
        
        part1, part2 = parts
        
        # Fix first part to be more numeric
        part1_fixed = ""
        for char in part1:
            if char == 'O':
                part1_fixed += '0'  # O -> 0
            elif char == 'I':
                part1_fixed += '1'  # I -> 1
            elif char == 'S':
                part1_fixed += '5'  # S -> 5
            elif char == 'J':
                part1_fixed += '1'  # J -> 1 (common OCR error)
            elif char == 'G':
                part1_fixed += '6'  # G -> 6
            elif char == 'B':
                part1_fixed += '8'  # B -> 8
            elif char == 'Z':
                part1_fixed += '2'  # Z -> 2
            elif char == 'T':
                part1_fixed += '7'  # T -> 7
            else:
                part1_fixed += char
        
        # Fix second part to be more alphabetic
        part2_fixed = ""
        for char in part2:
            if char == '0':
                part2_fixed += 'O'  # 0 -> O
            elif char == '1':
                part2_fixed += 'I'  # 1 -> I
            elif char == '5':
                part2_fixed += 'S'  # 5 -> S
            elif char == '4':
                part2_fixed += 'A'  # 4 -> A (common OCR error)
            elif char == '6':
                part2_fixed += 'G'  # 6 -> G
            elif char == '8':
                part2_fixed += 'B'  # 8 -> B
            elif char == '2':
                part2_fixed += 'Z'  # 2 -> Z
            elif char == '7':
                part2_fixed += 'T'  # 7 -> T
            else:
                part2_fixed += char
        
        return f"{part1_fixed} {part2_fixed}"
    
    @classmethod
    def _is_valid_format(cls, text: str) -> bool:
        """Check if text matches valid Philippine license plate format"""
        if not text or ' ' not in text:
            return False
        
        parts = text.split(' ')
        if len(parts) != 2:
            return False
        
        part1, part2 = parts
        if len(part1) != 3 or len(part2) != 3:
            return False
        
        # Check for invalid characters (no dashes, underscores, etc.)
        if re.search(r'[^A-Z0-9\s]', text):
            return False
        
        # Must match either ### XXX or XXX ### format
        pattern1 = r'^[0-9]{3}\s[A-Z]{3}$'  # 123 ABC
        pattern2 = r'^[A-Z]{3}\s[0-9]{3}$'  # ABC 123
        
        return bool(re.match(pattern1, text) or re.match(pattern2, text))
    
    @classmethod
    def _get_plate_type(cls, text: str) -> str:
        """Get plate type"""
        if not cls._is_valid_format(text):
            return "invalid"
        
        parts = text.split(' ')
        part1, part2 = parts
        
        if re.match(r'^[0-9]{3}$', part1) and re.match(r'^[A-Z]{3}$', part2):
            return "numeric_alpha"  # 123 ABC
        elif re.match(r'^[A-Z]{3}$', part1) and re.match(r'^[0-9]{3}$', part2):
            return "alpha_numeric"  # ABC 123
        else:
            return "unknown"

# Convenience functions for backward compatibility
def is_valid_plate(plate_text: str) -> bool:
    """Quick validation check"""
    is_valid, _, _ = PlateValidator.validate_and_normalize(plate_text)
    return is_valid

def normalize_plate(plate_text: str) -> Optional[str]:
    """Quick normalization"""
    _, normalized, _ = PlateValidator.validate_and_normalize(plate_text)
    return normalized

def validate_plate(plate_text: str) -> tuple[bool, Optional[str], str]:
    """Complete validation"""
    return PlateValidator.validate_and_normalize(plate_text)

# Test the validator
if __name__ == "__main__":
    test_plates = [
        'J00 OO4',  # Should become 100 OOA
        '518 UOZ',  # Already valid
        'ABC 123',  # Already valid  
        '5I8 U0Z',  # Should become 518 UOZ
        'AB0 I23',  # Should become AB0 123
        'O12 ABC',  # Should become 012 ABC
        'I23 S56',  # Should become 123 556
        '518-UOZ',  # Invalid (has dash)
        'PLATE_123', # Invalid
    ]
    
    print('🧪 OCR Error Correction Test:')
    print('Original    | Valid | Normalized | Type')
    print('-' * 45)
    
    for plate in test_plates:
        is_valid, normalized, plate_type = validate_plate(plate)
        status = '✅' if is_valid else '❌'
        print(f'{status} {plate:10} | {str(is_valid):5} | {normalized or "None":10} | {plate_type}')
