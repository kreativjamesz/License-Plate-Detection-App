import json
import os
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from threading import Lock, Thread
import queue

class DetectionLogger:
    """
    Fast logging system for license plate detections
    - Logs detections to JSON file immediately (no database delay)
    - Separate thread batches data to database every 10 seconds
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.logs_queue = queue.Queue()
        self.file_lock = Lock()
        self.running = False
        self.batch_thread = None
        self.last_save_time = 0
        self.save_interval = 3.0  # Still 3 seconds between detections
        self.batch_interval = 10.0  # 10 seconds batch to database
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Today's log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.current_log_file = os.path.join(self.log_dir, f"detections_{today}.json")
        
        print(f"📝 Detection logger initialized: {self.current_log_file}")
    
    def can_log_detection(self) -> bool:
        """Check if enough time passed since last detection (3 second rule)"""
        current_time = time.time()
        return (current_time - self.last_save_time) >= self.save_interval
    
    def log_detection(self, plate_text: str = "", confidence: float = 0.0,
                     location: str = "Camera", coordinates: Tuple[int, int, int, int] = None) -> bool:
        """
        Log detection to JSON file immediately (FAST operation)
        Returns True if logged, False if skipped due to 3-second rule
        """
        if not self.can_log_detection():
            return False  # Skip - too soon
        
        try:
            current_time = time.time()
            detection_data = {
                "id": f"det_{int(current_time * 1000)}",  # Unique ID based on timestamp
                "plate_text": plate_text or f"PLATE_{int(current_time)}",
                "confidence": round(confidence, 2),
                "location": location,
                "coordinates": {
                    "x": coordinates[0] if coordinates else 0,
                    "y": coordinates[1] if coordinates else 0,
                    "w": coordinates[2] if coordinates else 0,
                    "h": coordinates[3] if coordinates else 0
                } if coordinates else None,
                "timestamp": datetime.now().isoformat(),
                "unix_time": current_time,
                "status": "detected",
                "processed": False  # Flag for database processing
            }
            
            # Write to log file immediately (FAST)
            self._write_to_log_file(detection_data)
            
            # Add to queue for database processing
            self.logs_queue.put(detection_data)
            
            # Update last save time
            self.last_save_time = current_time
            
            print(f"📝 Logged: {detection_data['plate_text']} (Queue: {self.logs_queue.qsize()})")
            return True
            
        except Exception as e:
            print(f"❌ Logging error: {e}")
            return False
    
    def _write_to_log_file(self, detection_data: Dict):
        """Write detection to JSON log file immediately"""
        try:
            with self.file_lock:
                # Check if file exists and has content
                if os.path.exists(self.current_log_file):
                    with open(self.current_log_file, 'r', encoding='utf-8') as f:
                        try:
                            log_data = json.load(f)
                        except json.JSONDecodeError:
                            log_data = {"detections": []}
                else:
                    log_data = {"detections": []}
                
                # Add new detection
                log_data["detections"].append(detection_data)
                
                # Write back to file
                with open(self.current_log_file, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"❌ File write error: {e}")
    
    def start_batch_processor(self):
        """Start background thread for batch processing to database"""
        if self.running:
            return
            
        self.running = True
        self.batch_thread = Thread(target=self._batch_processor_loop, daemon=True)
        self.batch_thread.start()
        print(f"🚀 Started batch processor (every {self.batch_interval} seconds)")
    
    def stop_batch_processor(self):
        """Stop background batch processor"""
        self.running = False
        if self.batch_thread:
            self.batch_thread.join(timeout=2)
        print("🛑 Stopped batch processor")
    
    def _batch_processor_loop(self):
        """Background loop that processes queued detections to database every 10 seconds"""
        last_batch_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time for batch processing
                if (current_time - last_batch_time) >= self.batch_interval:
                    self._process_batch_to_database()
                    last_batch_time = current_time
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Batch processor error: {e}")
                time.sleep(1)
    
    def _process_batch_to_database(self):
        """Process all queued detections to database"""
        if self.logs_queue.empty():
            return
        
        batch_detections = []
        
        # Collect all queued items
        while not self.logs_queue.empty():
            try:
                detection = self.logs_queue.get_nowait()
                batch_detections.append(detection)
            except queue.Empty:
                break
        
        if not batch_detections:
            return
        
        print(f"💾 Processing batch of {len(batch_detections)} detections to database...")
        
        try:
            # Import here to avoid circular imports
            from app.services.license_plate_service import LicensePlateService
            
            service = LicensePlateService()
            saved_count = 0
            
            for detection in batch_detections:
                coords = None
                if detection.get('coordinates'):
                    c = detection['coordinates']
                    coords = (c['x'], c['y'], c['w'], c['h'])
                
                # Save to database (bypass the time check since we're batching)
                plate_id = service.add_detection(
                    plate_text=detection['plate_text'],
                    confidence=detection['confidence'],
                    location=detection['location'],
                    coordinates=coords
                )
                
                if plate_id > 0:
                    saved_count += 1
                    # Mark as processed in log file
                    detection['processed'] = True
                    detection['database_id'] = plate_id
            
            print(f"✅ Batch processed: {saved_count}/{len(batch_detections)} saved to database")
            
            # Update log file with processed flags
            self._update_log_file_processed_flags(batch_detections)
            
        except Exception as e:
            print(f"❌ Batch processing error: {e}")
            # Put items back in queue for retry
            for detection in batch_detections:
                self.logs_queue.put(detection)
    
    def _update_log_file_processed_flags(self, processed_detections: List[Dict]):
        """Update log file to mark detections as processed"""
        try:
            with self.file_lock:
                if not os.path.exists(self.current_log_file):
                    return
                
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # Update processed flags
                processed_ids = {det['id'] for det in processed_detections}
                for detection in log_data.get('detections', []):
                    if detection['id'] in processed_ids:
                        detection['processed'] = True
                        # Find matching detection for database_id
                        for proc_det in processed_detections:
                            if proc_det['id'] == detection['id']:
                                detection['database_id'] = proc_det.get('database_id')
                                break
                
                # Write back
                with open(self.current_log_file, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"❌ Error updating log file: {e}")
    
    def get_today_detections_count(self) -> int:
        """Get count of today's detections from log file"""
        try:
            if not os.path.exists(self.current_log_file):
                return 0
                
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                return len(log_data.get('detections', []))
                
        except Exception as e:
            print(f"❌ Error reading log count: {e}")
            return 0
    
    def get_recent_detections(self, limit: int = 5) -> List[Dict]:
        """Get recent detections from log file"""
        try:
            if not os.path.exists(self.current_log_file):
                return []
                
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                detections = log_data.get('detections', [])
                # Return most recent first
                return detections[-limit:][::-1]
                
        except Exception as e:
            print(f"❌ Error reading recent detections: {e}")
            return []

# Global logger instance
detection_logger = DetectionLogger()

def start_detection_logging():
    """Start the detection logging system"""
    detection_logger.start_batch_processor()

def stop_detection_logging():
    """Stop the detection logging system"""
    detection_logger.stop_batch_processor()

def log_plate_detection(plate_text: str = "", confidence: float = 0.0,
                       location: str = "Camera", coordinates: Tuple[int, int, int, int] = None) -> bool:
    """Convenience function to log a plate detection"""
    return detection_logger.log_detection(plate_text, confidence, location, coordinates)
