from plate_validator_simple import SimplePlateValidator

validator = SimplePlateValidator()

test = 'J00 OO4'
print(f'Testing: {test}')
is_valid, normalized, plate_type = validator.validate_and_normalize(test)
print(f'Result: Valid={is_valid}, Normalized={normalized}, Type={plate_type}')

# Debug the correction
fixed = validator._fix_ocr_errors('J00 OO4')
print(f'After OCR fix: {fixed}')
