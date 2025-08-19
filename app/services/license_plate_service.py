from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
import time
from app.database.database_service import DatabaseService
from app.services.pagination import PaginationParams, PaginationResult

class LicensePlateService:
    """Service for managing license plate detection records using MySQL"""
    
    def __init__(self):
        self.last_save_time = 0  # Track last save time to prevent spam
        self.save_interval = 3.0  # 3 seconds between saves
    
    def can_save_detection(self) -> bool:
        """Check if enough time has passed to save a new detection (3 second interval)"""
        current_time = time.time()
        return (current_time - self.last_save_time) >= self.save_interval
    
    def add_detection_if_allowed(self, plate_text: str = "", confidence: float = 0.0, 
                                location: str = "Camera", coordinates: Tuple[int, int, int, int] = None) -> Optional[int]:
        """Add detection only if 3 seconds have passed since last save"""
        if not self.can_save_detection():
            return None  # Skip saving, too soon
        
        return self.add_detection(plate_text, confidence, location, coordinates)
    
    def add_detection(self, plate_text: str = "", confidence: float = 0.0, 
                     location: str = "Camera", coordinates: Tuple[int, int, int, int] = None) -> int:
        """Add a new license plate detection record to MySQL"""
        try:
            current_time = time.time()
            
            # Simple plate text - just use detected coordinates or assign a number
            if not plate_text:
                # Generate a unique plate number
                conn = DatabaseService.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM license_plates")
                count = cursor.fetchone()[0]
                plate_text = f"PLATE_{count + 1:04d}"
                cursor.close()
                conn.close()
            
            # Prepare coordinates as JSON
            coords_json = None
            if coordinates:
                coords_json = json.dumps({
                    "x": coordinates[0],
                    "y": coordinates[1], 
                    "w": coordinates[2],
                    "h": coordinates[3]
                })
            
            # Insert into database
            conn = DatabaseService.get_connection()
            cursor = conn.cursor()
            
            insert_query = """
                INSERT INTO license_plates (plate_text, confidence, location, coordinates, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                plate_text,
                round(confidence, 2),
                location,
                coords_json,
                'detected'
            ))
            
            plate_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update last save time
            self.last_save_time = current_time
            
            print(f"✅ Added license plate detection: {plate_text} (ID: {plate_id})")
            return plate_id
            
        except Exception as e:
            print(f"❌ Error adding plate detection: {e}")
            return -1
    
    def get_plates_for_table(self) -> List[List[str]]:
        """Get license plate data formatted for table display"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id, plate_text, location, 
                       DATE(detected_at) as date_detected,
                       TIME(detected_at) as time_detected,
                       status
                FROM license_plates 
                ORDER BY detected_at DESC
            """
            
            cursor.execute(query)
            plates = cursor.fetchall()
            cursor.close()
            conn.close()
            
            table_data = []
            for plate in plates:
                row = [
                    str(plate['id']),
                    plate['plate_text'],
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
                    WHERE (plate_text LIKE %s OR location LIKE %s OR status LIKE %s)
                """
                search_term = f"%{params.search_term}%"
                search_params = [search_term, search_term, search_term]
            
            # Build ORDER BY clause
            order_direction = "DESC" if params.sort_order.upper() == "DESC" else "ASC"
            if params.sort_by == "plate_text":
                order_clause = f"ORDER BY plate_text {order_direction}"
            elif params.sort_by == "confidence":
                order_clause = f"ORDER BY confidence {order_direction}"
            else:
                order_clause = f"ORDER BY id {order_direction}"
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM license_plates {where_clause}"
            cursor.execute(count_query, search_params)
            total_items = cursor.fetchone()['total']
            
            # Calculate pagination
            total_pages = (total_items + params.limit - 1) // params.limit
            offset = (params.page - 1) * params.limit
            
            # Get page data
            data_query = f"""
                SELECT id, plate_text, 
                       DATE(detected_at) as date_detected,
                       TIME(detected_at) as time_detected,
                       location, status
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
                    plate['plate_text'],
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
                print(f"✅ Updated plate {plate_id}")
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
                    SUM(CASE WHEN status = 'detected' THEN 1 ELSE 0 END) as detected,
                    SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END) as verified,
                    SUM(CASE WHEN status = 'flagged' THEN 1 ELSE 0 END) as flagged
                FROM license_plates
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return {
                'total': result['total'] or 0,
                'detected': result['detected'] or 0,
                'verified': result['verified'] or 0,
                'flagged': result['flagged'] or 0
            }
            
        except Exception as e:
            print(f"❌ Error getting plate stats: {e}")
            return {'total': 0, 'detected': 0, 'verified': 0, 'flagged': 0}
    
    def get_todays_detections(self) -> List[Dict]:
        """Get today's license plate detections"""
        try:
            conn = DatabaseService.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * FROM license_plates 
                WHERE DATE(detected_at) = CURDATE()
                ORDER BY detected_at DESC
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
                   OR location LIKE %s 
                   OR status LIKE %s 
                   OR notes LIKE %s
                ORDER BY detected_at DESC
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