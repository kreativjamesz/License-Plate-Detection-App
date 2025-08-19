import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import os

class PlateDetector:
    """License plate detector using multiple haarcascade models"""
    
    def __init__(self):
        self.models_path = "app/models/"
        self.cascade_models = {}
        self._load_cascade_models()
    
    def _load_cascade_models(self):
        """Load all available license plate cascade models"""
        # Available license plate models
        plate_models = {
            "russian_plate": "haarcascade_russian_plate_number.xml",
            "russian_16_stages": "haarcascade_license_plate_rus_16stages.xml"
        }
        
        for model_name, filename in plate_models.items():
            model_path = os.path.join(self.models_path, filename)
            if os.path.exists(model_path):
                try:
                    cascade = cv2.CascadeClassifier(model_path)
                    if not cascade.empty():
                        self.cascade_models[model_name] = cascade
                        print(f"✅ Loaded {model_name} plate detection model")
                    else:
                        print(f"⚠️ Failed to load {model_name} - cascade is empty")
                except Exception as e:
                    print(f"❌ Error loading {model_name}: {e}")
            else:
                print(f"⚠️ Model file not found: {model_path}")
        
        if not self.cascade_models:
            print("❌ No license plate detection models loaded!")
        else:
            print(f"✅ Total {len(self.cascade_models)} plate detection models loaded")
    
    def detect_plates(self, frame: np.ndarray, model_name: str = None) -> List[Tuple[int, int, int, int]]:
        """
        Detect license plates in frame
        
        Args:
            frame: Input image/frame
            model_name: Specific model to use (None = use all models)
            
        Returns:
            List of (x, y, w, h) tuples representing detected plates
        """
        if len(self.cascade_models) == 0:
            print("⚠️ No cascade models available for plate detection")
            return []
        
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        all_plates = []
        
        # Use specific model if requested
        if model_name and model_name in self.cascade_models:
            plates = self._detect_with_model(gray, self.cascade_models[model_name], model_name)
            all_plates.extend(plates)
        else:
            # Use all available models and combine results
            for name, cascade in self.cascade_models.items():
                plates = self._detect_with_model(gray, cascade, name)
                all_plates.extend(plates)
        
        # Remove duplicate detections
        filtered_plates = self._filter_overlapping_plates(all_plates)
        
        return filtered_plates
    
    def _detect_with_model(self, gray_frame: np.ndarray, cascade: cv2.CascadeClassifier, 
                          model_name: str) -> List[Tuple[int, int, int, int]]:
        """Detect plates using a specific cascade model"""
        try:
            # Different parameters for different models
            if "russian" in model_name:
                # Parameters tuned for Russian license plates
                plates = cascade.detectMultiScale(
                    gray_frame,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(50, 15),   # License plates are wider than tall
                    maxSize=(300, 100),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
            else:
                # Default parameters
                plates = cascade.detectMultiScale(
                    gray_frame,
                    scaleFactor=1.2,
                    minNeighbors=3,
                    minSize=(40, 15),
                    maxSize=(400, 120),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
            
            # Add model name info to each detection
            plates_with_info = []
            for (x, y, w, h) in plates:
                plates_with_info.append((x, y, w, h))
            
            if len(plates) > 0:
                print(f"🔍 {model_name}: Found {len(plates)} potential plates")
            
            return plates_with_info
            
        except Exception as e:
            print(f"❌ Error detecting with {model_name}: {e}")
            return []
    
    def _filter_overlapping_plates(self, plates: List[Tuple[int, int, int, int]], 
                                 overlap_threshold: float = 0.3) -> List[Tuple[int, int, int, int]]:
        """Remove overlapping detections using Non-Maximum Suppression"""
        if len(plates) <= 1:
            return plates
        
        # Convert to numpy array for easier manipulation
        boxes = np.array(plates)
        
        # Calculate areas
        areas = boxes[:, 2] * boxes[:, 3]
        
        # Sort by confidence (we'll use area as a proxy)
        indices = np.argsort(areas)[::-1]
        
        keep = []
        while len(indices) > 0:
            # Pick the detection with largest area
            current = indices[0]
            keep.append(current)
            
            if len(indices) == 1:
                break
            
            # Calculate IoU with remaining detections
            remaining = indices[1:]
            ious = []
            
            for idx in remaining:
                iou = self._calculate_iou(boxes[current], boxes[idx])
                ious.append(iou)
            
            # Keep only detections with IoU below threshold
            ious = np.array(ious)
            indices = remaining[ious < overlap_threshold]
        
        return [plates[i] for i in keep]
    
    def _calculate_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """Calculate Intersection over Union of two bounding boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def draw_plates(self, frame: np.ndarray, plates: List[Tuple[int, int, int, int]], 
                   color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """Draw bounding boxes around detected plates"""
        result_frame = frame.copy()
        
        for i, (x, y, w, h) in enumerate(plates):
            # Draw rectangle
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, thickness)
            
            # Add label
            label = f"Plate {i+1}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Draw label background
            cv2.rectangle(result_frame, 
                         (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), 
                         color, -1)
            
            # Draw label text
            cv2.putText(result_frame, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result_frame
    
    def get_available_models(self) -> List[str]:
        """Get list of available detection models"""
        return list(self.cascade_models.keys())
    
    def extract_plate_roi(self, frame: np.ndarray, plate_coords: Tuple[int, int, int, int], 
                         padding: int = 10) -> Optional[np.ndarray]:
        """Extract license plate region of interest with padding"""
        x, y, w, h = plate_coords
        
        # Add padding
        x_start = max(0, x - padding)
        y_start = max(0, y - padding)
        x_end = min(frame.shape[1], x + w + padding)
        y_end = min(frame.shape[0], y + h + padding)
        
        # Extract ROI
        roi = frame[y_start:y_end, x_start:x_end]
        
        return roi if roi.size > 0 else None

# Global detector instance
plate_detector = PlateDetector()

def detect_license_plates(frame: np.ndarray, model_name: str = None) -> List[Tuple[int, int, int, int]]:
    """Convenience function for detecting license plates"""
    return plate_detector.detect_plates(frame, model_name)

def draw_detected_plates(frame: np.ndarray, plates: List[Tuple[int, int, int, int]]) -> np.ndarray:
    """Convenience function for drawing detected plates"""
    return plate_detector.draw_plates(frame, plates)
