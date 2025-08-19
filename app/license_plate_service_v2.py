from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
import time
from app.database.database_service import DatabaseService
from app.services.pagination import PaginationParams, PaginationResult

class LicensePlateService:
    """Service for managing license plate detection records with duplicate prevention"""
    
    def __init__(self):
        self.last_save_time = 0
        self.save_interval = 3.0
    
    def can_save_detection(self) -> bool:
        """Check if enough time has passed to save a new detection (3 second interval)"""
        current_time = time.time()
        return (current_time - self.last_save_time) >= self.save_interval
    
    def find_recent_detection(self, plate_text: str, time_window_minutes: int = 10) -> Optional[Dict]:
        """Find recent detection of the same plate within time window"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * FROM license_plates 
                WHERE plate_text = %s 
                AND last_seen >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
                ORDER BY last_seen DESC 
                LIMIT 1
            """
            
            cursor.execute(query, (plate_text, time_window_minutes))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result
            
        except Exception as e:
            print(f"❌ Error finding recent detection: {e}")
            return None
    
    def add_detection_if_allowed(self, plate_text: str = "", confidence: float = 0.0, 
                                location: str = "Camera", coordinates: Tuple[int, int, int, int] = None) -> Optional[int]:
        """Add detection only if 3 seconds have passed since last save"""
        if not self.can_save_detection():
            return None  # Skip saving, too soon
        
        plate_id, is_new = self.add_or_update_detection(plate_text, confidence, location, coordinates)
        return plate_id if plate_id > 0 else None
    
    def add_or_update_detection(self, plate_text: str = "", confidence: float = 0.0, 
                               location: str = "Camera", coordinates: Tuple[int, int, int, int] = None) -> Tuple[int, bool]:
        """
        Add new detection or update existing one if found recently
        Returns: (plate_id, is_new_record)
        """
        try:
            current_time = time.time()
            
            # Generate plate text if empty
            if not plate_text:
                conn = DatabaseService.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM license_plates")
                count = cursor.fetchone()[0]
                plate_text = f"PLATE_{count + 1:04d}"
                cursor.close()
                conn.close()
            
            # Check for recent detection of the same plate (within 10 minutes)
            recent_detection = self.find_recent_detection(plate_text, time_window_minutes=10)
            
            if recent_detection:
                # UPDATE existing detection
                plate_id = recent_detection['id']
                
                # Prepare update data
                update_data = {}
                
                # Always increment detection count
                new_count = recent_detection.get('detection_count', 1) + 1
                update_data['detection_count'] = new_count
                
                # Update best confidence if this one is better
                best_conf = recent_detection.get('best_confidence', 0.0)
                if confidence > best_conf:
                    update_data['best_confidence'] = confidence
                    # Also update best coordinates
                    if coordinates:
                        coords_json = json.dumps({
                            "x": coordinates[0], "y": coordinates[1], 
                            "w": coordinates[2], "h": coordinates[3]
                        })
                        update_data['best_coordinates'] = coords_json
                
                # Always update current confidence and coordinates
                update_data['confidence'] = confidence
                if coordinates:
                    coords_json = json.dumps({
                        "x": coordinates[0], "y": coordinates[1], 
                        "w": coordinates[2], "h": coordinates[3]
                    })
                    update_data['coordinates'] = coords_json
                
                # Update location info
                update_data['latest_location'] = location
                update_data['last_seen'] = datetime.now()
                
                # Update the record
                success = self.update_plate(plate_id, update_data)
                if success:
                    print(f"��� Updated existing plate: {plate_text} (ID: {plate_id}, Count: {new_count}, Conf: {confidence})")
                    self.last_save_time = current_time
                    return plate_id, False  # Not new record
                
                return plate_id, False
            
            else:
                # CREATE new detection
                plate_id = self._create_new_detection(plate_text, confidence, location, coordinates)
                if plate_id > 0:
                    self.last_save_time = current_time
                    return plate_id, True  # New record
                
                return -1, False
                
        except Exception as e:
            print(f"❌ Error in add_or_update_detection: {e}")
            return -1, False
    
    def _create_new_detection(self, plate_text: str, confidence: float, location: str, 
                             coordinates: Tuple[int, int, int, int] = None) -> int:
        """Create a new license plate detection record"""
        try:
            # Prepare coordinates as JSON
            coords_json = None
            if coordinates:
                coords_json = json.dumps({
                    "x": coordinates[0], "y": coordinates[1], 
                    "w": coordinates[2], "h": coordinates[3]
                })
            
            # Insert into database
            conn = DatabaseService.get_connection()
            cursor = conn.cursor()
            
            insert_query = """
                INSERT INTO license_plates (
                    plate_text, confidence, best_confidence, location, coordinates, 
                    best_coordinates, status, detection_count, first_location, latest_location
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                plate_text,
                round(confidence, 2),
                round(confidence, 2),  # best_confidence starts same as confidence
                location,
                coords_json,
                coords_json,  # best_coordinates starts same as coordinates
                'detected',
                1,  # detection_count starts at 1
                location,  # first_location
                location   # latest_location
            ))
            
            plate_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Created new license plate: {plate_text} (ID: {plate_id})")
            return plate_id
            
        except Exception as e:
            print(f"❌ Error creating new detection: {e}")
            return -1
    
    def add_detection(self, plate_text: str = "", confidence: float = 0.0, 
                     location: str = "Camera", coordinates: Tuple[int, int, int, int] = None) -> int:
        """Legacy method - now uses add_or_update_detection"""
        plate_id, _ = self.add_or_update_detection(plate_text, confidence, location, coordinates)
        return plate_id
    
    def get_plates_for_table(self) -> List[List[str]]:
        """Get license plate data formatted for table display"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id, plate_text, latest_location as location, 
                       DATE(last_seen) as date_detected,
                       TIME(last_seen) as time_detected,
                       status, detection_count, best_confidence
                FROM license_plates 
                ORDER BY last_seen DESC
            """
            
            cursor.execute(query)
            plates = cursor.fetchall()
            cursor.close()
            conn.close()
            
            table_data = []
            for plate in plates:
                row = [
                    str(plate['id']),
                    f"{plate['plate_text']} ({plate['detection_count']}x)",  # Show detection count
                    str(plate['date_detected']),
                    str(plate['time_detected']),
                    plate['location'],
                    plate['status'].title()
                ]
                table_data.append(row)
            
            return table_data
            
        except Exception as e:
            print(f"❌ Error getting plates for table: {e}")
            return []
    
    def get_plates_for_table_paginated(self, params: PaginationParams) -> Tuple[List[List[str]], PaginationResult]:
        """Get paginated license plate data for table display"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Build WHERE clause for search
            where_clause = ""
            search_params = []
            
            if params.search_term:
                where_clause = """
                    WHERE (plate_text LIKE %s OR latest_location LIKE %s OR status LIKE %s)
                """
                search_term = f"%{params.search_term}%"
                search_params = [search_term, search_term, search_term]
            
            # Build ORDER BY clause
            order_direction = "DESC" if params.sort_order.upper() == "DESC" else "ASC"
            if params.sort_by == "plate_text":
                order_clause = f"ORDER BY plate_text {order_direction}"
            elif params.sort_by == "confidence":
                order_clause = f"ORDER BY best_confidence {order_direction}"
            elif params.sort_by == "detection_count":
                order_clause = f"ORDER BY detection_count {order_direction}"
            else:
                order_clause = f"ORDER BY last_seen {order_direction}"
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM license_plates {where_clause}"
            cursor.execute(count_query, search_params)
            total_items = cursor.fetchone()['total']
            
            # Calculate pagination
            total_pages = (total_items + params.limit - 1) // params.limit
            offset = (params.page - 1) * params.limit
            
            # Get page data
            data_query = f"""
                SELECT id, plate_text, latest_location as location,
                       DATE(last_seen) as date_detected,
                       TIME(last_seen) as time_detected,
                       status, detection_count, best_confidence
                FROM license_plates 
                {where_clause}
                {order_clause}
                LIMIT %s OFFSET %s
            """
            
            query_params = search_params + [params.limit, offset]
            cursor.execute(data_query, query_params)
            plates = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Format for table
            table_data = []
            for plate in plates:
                row = [
                    str(plate['id']),
                    f"{plate['plate_text']} ({plate['detection_count']}x)",  # Show detection count
                    str(plate['date_detected']),
                    str(plate['time_detected']),
                    plate['location'],
                    plate['status'].title()
                ]
                table_data.append(row)
            
            # Create pagination result
            pagination_result = PaginationResult(
                page=params.page,
                limit=params.limit,
                total_items=total_items,
                total_pages=total_pages,
                has_next=params.page < total_pages,
                has_prev=params.page > 1
            )
            
            return table_data, pagination_result
            
        except Exception as e:
            print(f"❌ Error getting paginated plates: {e}")
            return [], PaginationResult(1, params.limit, 0, 0, False, False)
    
    def get_table_headers(self) -> List[str]:
        """Get table headers for license plate data"""
        return ["ID", "Plate Number", "Date", "Time", "Location", "Status"]
    
    def get_plate_by_id(self, plate_id: int) -> Optional[Dict]:
        """Get license plate record by ID"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM license_plates WHERE id = %s"
            cursor.execute(query, (plate_id,))
            plate = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return plate
            
        except Exception as e:
            print(f"❌ Error getting plate by ID: {e}")
            return None
    
    def update_plate(self, plate_id: int, updates: Dict) -> bool:
        """Update license plate record"""
        try:
            if not updates:
                return False
            
            conn = DatabaseService.get_connection()
            cursor = conn.cursor()
            
            # Build update query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                if key != 'id':  # Don't allow ID changes
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            # Add updated_at timestamp
            set_clauses.append("updated_at = NOW()")
            values.append(plate_id)
            
            query = f"UPDATE license_plates SET {', '.join(set_clauses)} WHERE id = %s"
            cursor.execute(query, values)
            
            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if rows_affected > 0:
                return True
            else:
                print(f"⚠️ Plate {plate_id} not found")
                return False
            
        except Exception as e:
            print(f"❌ Error updating plate: {e}")
            return False
    
    def delete_plate(self, plate_id: int) -> bool:
        """Delete license plate record"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor()
            
            query = "DELETE FROM license_plates WHERE id = %s"
            cursor.execute(query, (plate_id,))
            
            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if rows_affected > 0:
                print(f"✅ Deleted plate {plate_id}")
                return True
            else:
                print(f"⚠️ Plate {plate_id} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting plate: {e}")
            return False
    
    def get_plates_count(self) -> Dict[str, int]:
        """Get license plate statistics"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(detection_count) as total_detections,
                    SUM(CASE WHEN status = 'detected' THEN 1 ELSE 0 END) as detected,
                    SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified,
                    SUM(CASE WHEN status = 'flagged' THEN 1 ELSE 0 END) as flagged,
                    AVG(detection_count) as avg_detections_per_plate
                FROM license_plates
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return {
                'total': result['total'] or 0,
                'total_detections': result['total_detections'] or 0,
                'detected': result['detected'] or 0,
                'verified': result['verified'] or 0,
                'flagged': result['flagged'] or 0,
                'avg_detections': round(result['avg_detections_per_plate'] or 0, 1)
            }
            
        except Exception as e:
            print(f"❌ Error getting plate stats: {e}")
            return {'total': 0, 'total_detections': 0, 'detected': 0, 'verified': 0, 'flagged': 0, 'avg_detections': 0}
    
    def get_todays_detections(self) -> List[Dict]:
        """Get today's license plate detections"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * FROM license_plates 
                WHERE DATE(last_seen) = CURDATE()
                ORDER BY last_seen DESC
            """
            
            cursor.execute(query)
            plates = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return plates
            
        except Exception as e:
            print(f"❌ Error getting today's detections: {e}")
            return []
    
    def search_plates(self, query: str) -> List[Dict]:
        """Search license plates by text, location, or status"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            search_query = """
                SELECT * FROM license_plates 
                WHERE plate_text LIKE %s 
                   OR latest_location LIKE %s 
                   OR status LIKE %s 
                   OR notes LIKE %s
                ORDER BY last_seen DESC
            """
            
            search_term = f"%{query}%"
            cursor.execute(search_query, (search_term, search_term, search_term, search_term))
            plates = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return plates
            
        except Exception as e:
            print(f"❌ Error searching plates: {e}")
            return []
    
    def flag_plate(self, plate_id: int, reason: str = "") -> bool:
        """Flag a license plate for review"""
        return self.update_plate(plate_id, {
            'status': 'flagged',
            'flag_reason': reason,
            'flagged_at': datetime.now()
        })
    
    def verify_plate(self, plate_id: int, verified_text: str = None) -> bool:
        """Mark a license plate as verified"""
        updates = {
            'status': 'verified',
            'verified_at': datetime.now()
        }
        
        if verified_text:
            updates['plate_text'] = verified_text
            
        return self.update_plate(plate_id, updates)
