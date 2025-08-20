"""
OCR Service for License Plate Text Recognition
Uses EasyOCR to extract text from detected license plate regions
Optimized for Philippine license plate formats
"""

import easyocr
import cv2
import numpy as np
from typing import Optional, Tuple, List
import re
import time
from app.utils.plate_validator import PlateValidator

class LicensePlateOCR:
    """OCR service specifically optimized for license plate text recognition"""
    
    def __init__(self):
        # Initialize EasyOCR reader with English language
        # This will download the model on first use
        print("🔤 Initializing EasyOCR for license plate recognition...")
        try:
            self.reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have CUDA
            print("✅ EasyOCR initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize EasyOCR: {e}")
            self.reader = None
        
        # OCR confidence threshold - lowered to catch more plates
        self.confidence_threshold = 0.25  # Even lower for bordered plates
        
        # Statistics
        self.total_attempts = 0
        self.successful_reads = 0
        self.start_time = time.time()
    
    def preprocess_plate_image(self, image: np.ndarray, coordinates: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Preprocess the license plate region for better OCR accuracy
        """
        try:
            x, y, w, h = coordinates
            
            # Extract plate region with some padding
            padding = 5
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)
            
            plate_region = image[y1:y2, x1:x2]
            
            if plate_region.size == 0:
                return None
            
            # Resize for better OCR (make it larger)
            scale_factor = 4.0  # Increased for better text recognition
            new_width = int(plate_region.shape[1] * scale_factor)
            new_height = int(plate_region.shape[0] * scale_factor)
            
            if new_width > 0 and new_height > 0:
                plate_region = cv2.resize(plate_region, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Convert to grayscale if it's color
            if len(plate_region.shape) == 3:
                plate_region = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            
            # Apply image enhancements for better OCR - optimized for bordered plates
            # 1. Reduce noise but preserve borders
            plate_region = cv2.GaussianBlur(plate_region, (3, 3), 0)
            
            # 2. Try multiple threshold methods for bordered plates
            # Method 1: Standard adaptive threshold
            thresh1 = cv2.adaptiveThreshold(
                plate_region, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Method 2: Otsu's threshold for high contrast plates
            _, thresh2 = cv2.threshold(plate_region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Method 3: Inverted threshold for dark borders
            _, thresh3 = cv2.threshold(plate_region, 127, 255, cv2.THRESH_BINARY_INV)
            thresh3 = cv2.bitwise_not(thresh3)  # Invert back
            
            # Choose the best threshold based on plate characteristics
            # Count white pixels to determine which works best
            white_pixels1 = cv2.countNonZero(thresh1)
            white_pixels2 = cv2.countNonZero(thresh2)
            white_pixels3 = cv2.countNonZero(thresh3)
            
            # Use the threshold that gives moderate white pixel count (good character extraction)
            total_pixels = thresh1.shape[0] * thresh1.shape[1]
            white_ratios = [
                white_pixels1 / total_pixels,
                white_pixels2 / total_pixels,
                white_pixels3 / total_pixels
            ]
            
            # Prefer ratio between 0.3 and 0.7 (good character/background balance)
            best_idx = 0
            best_score = float('inf')
            for i, ratio in enumerate(white_ratios):
                # Score based on distance from ideal ratio (0.5)
                score = abs(ratio - 0.5)
                if 0.2 <= ratio <= 0.8 and score < best_score:
                    best_score = score
                    best_idx = i
            
            plate_region = [thresh1, thresh2, thresh3][best_idx]
            
            # 3. Morphological operations to clean up - smaller kernel for bordered plates
            kernel = np.ones((1, 1), np.uint8)
            plate_region = cv2.morphologyEx(plate_region, cv2.MORPH_CLOSE, kernel)
            
            # 4. Remove small noise while preserving character borders
            kernel = np.ones((2, 2), np.uint8)
            plate_region = cv2.morphologyEx(plate_region, cv2.MORPH_OPEN, kernel)
            
            return plate_region
            
        except Exception as e:
            print(f"❌ Error preprocessing plate image: {e}")
            return None
    
    def extract_text(self, image: np.ndarray, coordinates: Tuple[int, int, int, int]) -> Tuple[Optional[str], float]:
        """
        Extract text from a license plate region
        Returns: (extracted_text, confidence_score)
        """
        if self.reader is None:
            return None, 0.0
        
        self.total_attempts += 1
        
        try:
            # Preprocess the image
            processed_image = self.preprocess_plate_image(image, coordinates)
            
            if processed_image is None:
                return None, 0.0
            
            # Use EasyOCR to extract text with optimized parameters
            results = self.reader.readtext(
                processed_image,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ',  # Only alphanumeric and space
                width_ths=0.5,  # Lowered threshold for better detection
                height_ths=0.5,  # Lowered threshold for better detection
                paragraph=False,  # Don't group into paragraphs
                detail=1  # Return detailed results with confidence
            )
            
            if not results:
                return None, 0.0
            
            # Process all detected text regions
            best_text = None
            best_confidence = 0.0
            
            for (bbox, text, confidence) in results:
                # Clean up the text
                cleaned_text = self._clean_text(text)
                
                # Validate if it looks like a license plate
                if cleaned_text and confidence > self.confidence_threshold:
                    is_valid, normalized_text, plate_type = PlateValidator.validate_and_normalize(cleaned_text)
                    
                    if is_valid and confidence > best_confidence:
                        best_text = normalized_text
                        best_confidence = confidence
            
            if best_text:
                self.successful_reads += 1
                print(f"🔤 OCR Success: '{best_text}' (confidence: {best_confidence:.2f})")
                return best_text, best_confidence
            else:
                # Try fallback with lower threshold
                for (bbox, text, confidence) in results:
                    cleaned_text = self._clean_text(text)
                    if cleaned_text and len(cleaned_text) >= 5:  # At least 5 characters
                        print(f"🔤 OCR Fallback: '{cleaned_text}' (confidence: {confidence:.2f})")
                        return cleaned_text, confidence
                
                return None, 0.0
                
        except Exception as e:
            print(f"❌ OCR extraction error: {e}")
            return None, 0.0
    
    def _clean_text(self, text: str) -> Optional[str]:
        """Clean and normalize extracted text"""
        if not text:
            return None
        
        # Remove extra whitespace and convert to uppercase
        cleaned = text.strip().upper()
        
        # Remove common OCR errors and non-alphanumeric characters except space
        cleaned = re.sub(r'[^A-Z0-9\s]', '', cleaned)
        
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove leading/trailing spaces
        cleaned = cleaned.strip()
        
        # Must have at least 5 characters (minimum plate length)
        if len(cleaned) < 5:
            return None
        
        # Try to fix common OCR mistakes
        cleaned = self._fix_common_ocr_errors(cleaned)
        
        return cleaned if cleaned else None
    
    def _fix_common_ocr_errors(self, text: str) -> str:
        """Fix common OCR recognition errors"""
        # Common OCR character confusions
        corrections = {
            '0': 'O',  # Zero to O in some contexts
            'O': '0',  # O to zero in numeric contexts
            '1': 'I',  # One to I in letter contexts
            'I': '1',  # I to one in numeric contexts
            '5': 'S',  # Five to S in letter contexts
            'S': '5',  # S to five in numeric contexts
            '8': 'B',  # Eight to B in letter contexts
            'B': '8',  # B to eight in numeric contexts
        }
        
        # Apply context-aware corrections
        # If it looks like ### pattern, make sure first 3 are digits
        if len(text) >= 6 and ' ' in text:
            parts = text.split(' ')
            if len(parts) == 2:
                first_part, second_part = parts
                
                # First part should be 3 digits
                if len(first_part) == 3:
                    corrected_first = ''
                    for char in first_part:
                        if char in 'OILSB':
                            corrected_first += {'O': '0', 'I': '1', 'L': '1', 'S': '5', 'B': '8'}.get(char, char)
                        else:
                            corrected_first += char
                    first_part = corrected_first
                
                # Second part should be 3 letters
                if len(second_part) == 3:
                    corrected_second = ''
                    for char in second_part:
                        if char in '01585':
                            corrected_second += {'0': 'O', '1': 'I', '5': 'S', '8': 'B'}.get(char, char)
                        else:
                            corrected_second += char
                    second_part = corrected_second
                
                text = f"{first_part} {second_part}"
        
        return text
    
    def get_statistics(self) -> dict:
        """Get OCR performance statistics"""
        uptime = time.time() - self.start_time
        success_rate = (self.successful_reads / self.total_attempts * 100) if self.total_attempts > 0 else 0
        
        return {
            'total_attempts': self.total_attempts,
            'successful_reads': self.successful_reads,
            'success_rate': round(success_rate, 1),
            'uptime_seconds': round(uptime, 1)
        }
    
    def is_available(self) -> bool:
        """Check if OCR service is available"""
        return self.reader is not None

# Global OCR instance
ocr_service = LicensePlateOCR()

def extract_plate_text(image: np.ndarray, coordinates: Tuple[int, int, int, int]) -> Tuple[Optional[str], float]:
    """Convenience function to extract text from license plate region"""
    return ocr_service.extract_text(image, coordinates)

def get_ocr_stats() -> dict:
    """Get OCR performance statistics"""
    return ocr_service.get_statistics()

def is_ocr_available() -> bool:
    """Check if OCR is available"""
    return ocr_service.is_available()
