import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from tkinter import messagebox
from app.ui.widget.gradient_button import GradientButton
from app.ui.widget.data_table import DataTable
from app.services.license_plate_service import LicensePlateService
from app.services.plate.detector import plate_detector, detect_and_read_license_plates
from app.services.pagination import PaginationParams, PaginationService
from app.services.detection_logger import detection_logger, start_detection_logging, stop_detection_logging

class LicensePlatesPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.license_plate_service = LicensePlateService()
        self.camera = None
        self.camera_running = False
        self.detection_thread = None
        
        # Pagination state
        self.current_pagination_params = PaginationService.create_params(
            page=1,
            limit=25,
            sort_by="id",
            sort_order="DESC"  # Newest first
        )
        self.current_pagination_result = None
        
        try:
            self._build()
        except Exception as e:
            print(f"❌ Error building license plates page: {e}")
            self._build_fallback()
    
    def _build(self):
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header section
        header_frame = ctk.CTkFrame(self, corner_radius=15)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🚗 License Plate Detector",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=30, pady=20)
        
        # Camera controls
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e", padx=30, pady=20)
        
        try:
            self.start_btn = GradientButton(
                controls_frame,
                text="📷 Start Camera",
                command=self._start_camera,
                width=130,
                height=40,
                start_color="#10b981",
                end_color="#047857",
                corner_radius=20
            )
            self.start_btn.pack(side="left", padx=(0, 10))
            
            self.stop_btn = GradientButton(
                controls_frame,
                text="⏹️ Stop Camera",
                command=self._stop_camera,
                width=130,
                height=40,
                start_color="#ef4444",
                end_color="#dc2626",
                corner_radius=20
            )
            self.stop_btn.pack(side="left")
            self.stop_btn.configure(state="disabled")
        except:
            self.start_btn = ctk.CTkButton(
                controls_frame,
                text="📷 Start Camera",
                command=self._start_camera,
                width=130,
                height=40,
                fg_color="#10b981",
                corner_radius=20
            )
            self.start_btn.pack(side="left", padx=(0, 10))
            
            self.stop_btn = ctk.CTkButton(
                controls_frame,
                text="⏹️ Stop Camera",
                command=self._stop_camera,
                width=130,
                height=40,
                fg_color="#ef4444",
                corner_radius=20,
                state="disabled"
            )
            self.stop_btn.pack(side="left")
        
        # Main content area
        content_frame = ctk.CTkFrame(self, corner_radius=15)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Camera section
        camera_frame = ctk.CTkFrame(content_frame, corner_radius=10)
        camera_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        camera_frame.grid_columnconfigure(0, weight=1)
        camera_frame.grid_rowconfigure(1, weight=1)
        
        camera_title = ctk.CTkLabel(
            camera_frame,
            text="📹 Live Camera Feed",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        camera_title.grid(row=0, column=0, pady=(20, 10))
        
        # Camera display
        self.camera_label = ctk.CTkLabel(
            camera_frame,
            text="📷\n\nClick 'Start Camera' to begin\nlicense plate detection\n\n• Detects plates every 3 seconds\n• Shows live detection boxes\n• Auto-saves to database",
            font=ctk.CTkFont(size=16),
            text_color=("gray60", "gray40"),
            justify="center"
        )
        self.camera_label.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Detection status
        self.status_label = ctk.CTkLabel(
            camera_frame,
            text="🔴 Camera: Stopped",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ef4444"
        )
        self.status_label.grid(row=2, column=0, pady=(0, 15))
        
        # Detections table section
        table_frame = ctk.CTkFrame(content_frame, corner_radius=10)
        table_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(2, weight=1)
        
        # Table header with search
        table_header = ctk.CTkFrame(table_frame, fg_color="transparent")
        table_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        table_header.grid_columnconfigure(1, weight=1)
        
        table_title = ctk.CTkLabel(
            table_header,
            text="📋 Detected Plates",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        table_title.grid(row=0, column=0, sticky="w")
        
        # Search and controls
        search_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=14)
        )
        search_label.grid(row=0, column=0, sticky="w")
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search plates...",
            height=32,
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            search_frame,
            text="🔄",
            command=self._refresh_plates_data,
            width=40,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        refresh_btn.grid(row=0, column=2, sticky="e")
        
        # Plates table
        self.plates_table = DataTable(
            table_frame,
            headers=["ID", "Plate Number", "Date", "Time", "Location", "Status", "Actions"],
            data=[],
            height=350,
            on_select=self._on_plate_select,
            on_double_click=self._on_plate_double_click,
            on_edit=self._edit_plate_dialog,
            on_delete=self._delete_plate_dialog,
            searchable=False,
            show_toolbar=False,
            show_pagination=True,
            on_page_change=self._on_page_change,
            font_size=11,
            header_font_size=12
        )
        self.plates_table.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Statistics at bottom
        stats_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Current date
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        date_label = ctk.CTkLabel(
            stats_frame,
            text=f"📅 {current_date}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        date_label.grid(row=0, column=0, pady=10)
        
        # Load and display stats
        self._load_and_display_stats(stats_frame)
        
        # Load initial data
        self._load_plates_async()
    
    def _start_camera(self):
        """Start camera for license plate detection"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                messagebox.showerror("Error", "Cannot open camera!")
                return
            
            self.camera_running = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            
            self.status_label.configure(
                text="🟢 Camera: Running - Fast logging enabled...",
                text_color="#10b981"
            )
            
            # Start fast detection logging system
            start_detection_logging()
            
            # Start detection thread
            self.detection_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.detection_thread.start()
            
            print("✅ Camera started with fast logging system")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {e}")
            print(f"❌ Camera error: {e}")
    
    def _stop_camera(self):
        """Stop camera"""
        self.camera_running = False
        
        # Stop fast logging system
        stop_detection_logging()
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        self.status_label.configure(
            text="🔴 Camera: Stopped",
            text_color="#ef4444"
        )
        
        # Reset camera display
        self.camera_label.configure(
            text="📷\n\nCamera stopped\n\nClick 'Start Camera' to resume\nlicense plate detection",
            image=None
        )
        
        print("🛑 Camera and logging system stopped")
    
    def _camera_loop(self):
        """Main camera loop with OCR-enabled detection"""
        
        while self.camera_running and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Resize frame for better performance
                frame = cv2.resize(frame, (640, 480))
                
                # Detect and read license plates with OCR
                plate_results = detect_and_read_license_plates(frame)
                
                # Draw detection boxes with text
                display_frame = frame.copy()
                if plate_results:
                    display_frame = plate_detector.draw_plates_with_text(display_frame, plate_results)
                    
                    # Process each detected plate
                    for plate_info in plate_results:
                        coordinates = plate_info['coordinates']
                        plate_text = plate_info.get('text')
                        confidence = plate_info.get('confidence', 0.0)
                        is_valid = plate_info.get('valid', False)
                        
                        # Only log plates with valid OCR text
                        if is_valid and plate_text:
                            # Log to JSON file immediately (super fast)
                            logged = detection_logger.log_detection(
                                plate_text=plate_text,  # Use actual OCR text
                                confidence=confidence,   # Use actual OCR confidence
                                location="Camera",
                                coordinates=coordinates
                            )
                            
                            if logged:
                                print(f"🔤 Logged plate with OCR: '{plate_text}' (conf: {confidence:.2f})")
                                # Update UI to show recent log activity
                                self.after(0, self._update_detection_stats)
                            break  # Only process the first valid plate per frame
                        else:
                            # Skip plates without valid OCR text
                            if coordinates:
                                x, y, w, h = coordinates
                                print(f"🔍 Plate detected at ({x},{y}) but OCR failed - skipped")
                
                # Update camera display in UI thread
                self.after(0, lambda: self._update_camera_display(display_frame))
                
                # Control frame rate
                time.sleep(0.1)  # ~10 FPS
                
            except Exception as e:
                print(f"❌ Camera loop error: {e}")
                break
        
        print("📹 Camera loop ended")
    
    def _update_camera_display(self, frame):
        """Update camera display with current frame"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Resize to fit display
            display_size = (400, 300)
            pil_image = pil_image.resize(display_size, Image.Resampling.LANCZOS)
            
            # Convert to CTkImage for better scaling on HighDPI displays
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=display_size)
            
            # Update label
            self.camera_label.configure(image=ctk_image, text="")
            self.camera_label.image = ctk_image  # Keep reference
            
        except Exception as e:
            print(f"❌ Display update error: {e}")
    
    def _load_plates_async(self):
        """Load license plates data asynchronously"""
        def load_data():
            try:
                table_data, pagination_result = self.license_plate_service.get_plates_for_table_paginated(
                    self.current_pagination_params
                )
                
                # Add Actions column
                enhanced_data = []
                for row in table_data:
                    enhanced_row = list(row) + ["✏️ 🗑️"]
                    enhanced_data.append(enhanced_row)
                
                self.current_pagination_result = pagination_result
                
                # Update table in main thread
                self.after(0, lambda: self._update_table_with_pagination(enhanced_data, pagination_result))
                
            except Exception as e:
                print(f"❌ Error loading plates: {e}")
                self.after(0, lambda: self.plates_table.update_data(data=[["Error loading data", "", "", "", "", "", ""]]))
        
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()
    
    def _update_table_with_pagination(self, data, pagination_result):
        """Update table with data and pagination info"""
        self.plates_table.update_data(data=data)
        self.plates_table.update_pagination(pagination_result)
    
    def _on_page_change(self, page: int, limit: int = None):
        """Handle page change"""
        self.current_pagination_params.page = page
        if limit:
            self.current_pagination_params.limit = limit
        self._load_plates_async()
    
    def _on_search_change(self, event):
        """Handle search entry changes"""
        search_term = self.search_entry.get().strip()
        self.current_pagination_params.search_term = search_term
        self.current_pagination_params.page = 1
        
        if len(search_term) >= 2 or len(search_term) == 0:
            self._load_plates_async()
    
    def _refresh_plates_data(self):
        """Refresh plates data"""
        print("🔄 Refreshing plates data...")
        self._load_plates_async()
    
    def _on_plate_select(self, row_data):
        """Handle plate selection"""
        if row_data:
            plate_id = row_data[0]
            plate_text = row_data[1]
            print(f"📋 Selected plate: {plate_text} (ID: {plate_id})")
    
    def _on_plate_double_click(self, row_data):
        """Handle plate double click"""
        if row_data:
            self._edit_plate_dialog(row_data)
    
    def _edit_plate_dialog(self, row_data):
        """Edit plate dialog"""
        if not row_data:
            return
        
        plate_id = int(row_data[0])
        current_text = row_data[1]
        
        dialog = ctk.CTkInputDialog(
            text=f"Edit plate number (current: {current_text}):",
            title="Edit Plate"
        )
        new_text = dialog.get_input()
        
        if new_text and new_text != current_text:
            success = self.license_plate_service.update_plate(plate_id, {'plate_text': new_text})
            if success:
                messagebox.showinfo("Success", f"Updated plate to: {new_text}")
                self._refresh_plates_data()
            else:
                messagebox.showerror("Error", "Failed to update plate")
    
    def _delete_plate_dialog(self, row_data):
        """Delete plate dialog"""
        if not row_data:
            return
        
        plate_id = int(row_data[0])
        plate_text = row_data[1]
        
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Delete plate '{plate_text}'?\n\nThis cannot be undone."
        )
        
        if result:
            success = self.license_plate_service.delete_plate(plate_id)
            if success:
                messagebox.showinfo("Success", f"Deleted plate: {plate_text}")
                self._refresh_plates_data()
            else:
                messagebox.showerror("Error", "Failed to delete plate")
    
    def _load_and_display_stats(self, parent):
        """Load and display statistics"""
        self._create_stat_item(parent, "📊 Total Plates", "Loading...", 1)
        self._create_stat_item(parent, "✅ Detected", "Loading...", 2)
        self._create_stat_item(parent, "📅 Today", "Loading...", 3)
        
        self.stats_parent = parent
        
        def load_stats():
            try:
                stats = self.license_plate_service.get_plates_count()
                today_count = len(self.license_plate_service.get_todays_detections())
                
                display_stats = {
                    'total': stats.get('total', 0),
                    'detected': stats.get('detected', 0),
                    'today': today_count
                }
                
                self.after(0, lambda: self._update_stats_display(display_stats))
            except Exception as e:
                print(f"❌ Error loading stats: {e}")
                error_stats = {'total': 'Error', 'detected': 'Error', 'today': 'Error'}
                self.after(0, lambda: self._update_stats_display(error_stats))
        
        thread = threading.Thread(target=load_stats, daemon=True)
        thread.start()
    
    def _create_stat_item(self, parent, title, value, col):
        """Create a statistics item"""
        stat_frame = ctk.CTkFrame(parent, corner_radius=8)
        stat_frame.grid(row=0, column=col, sticky="ew", padx=5, pady=10)
        
        title_label = ctk.CTkLabel(
            stat_frame,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.pack(pady=(10, 2))
        
        value_label = ctk.CTkLabel(
            stat_frame,
            text=str(value),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1f538d", "#4a9eff")
        )
        value_label.pack(pady=(0, 10))
    
    def _update_detection_stats(self):
        """Update detection stats from log file"""
        try:
            today_count = detection_logger.get_today_detections_count()
            queue_size = detection_logger.logs_queue.qsize()
            
            # Update the status label to show activity
            if hasattr(self, 'status_label'):
                self.status_label.configure(
                    text=f"🟢 Camera: Running - {today_count} logged, {queue_size} queued",
                    text_color="#10b981"
                )
            
            # Refresh the data table less frequently to show database updates
            # The table will show database data, while logs show real-time activity
            
        except Exception as e:
            print(f"❌ Error updating detection stats: {e}")
    
    def _update_stats_display(self, stats):
        """Update existing stats display"""
        if hasattr(self, 'stats_parent') and self.stats_parent.winfo_exists():
            children = self.stats_parent.winfo_children()
            for widget in children[1:]:  # Skip date label
                widget.destroy()
            
            # Get today's log count for real-time stats
            today_log_count = detection_logger.get_today_detections_count()
            
            self._create_stat_item(self.stats_parent, "📊 Total Plates", str(stats.get('total', 0)), 1)
            self._create_stat_item(self.stats_parent, "✅ Detected", str(stats.get('detected', 0)), 2)
            self._create_stat_item(self.stats_parent, "📝 Today's Logs", str(today_log_count), 3)
    
    def _build_fallback(self):
        """Build fallback page when main build fails"""
        try:
            error_label = ctk.CTkLabel(
                self,
                text="⚠️ License Plates Page Error\n\nUnable to load page properly.\nPlease check your setup.",
                font=ctk.CTkFont(size=16),
                text_color=("gray60", "gray40"),
                justify="center"
            )
            error_label.pack(expand=True, fill="both", padx=50, pady=50)
        except Exception as e:
            print(f"❌ Error creating fallback page: {e}")
    
    def destroy(self):
        """Cleanup when page is destroyed"""
        if self.camera_running:
            self._stop_camera()
        
        # Stop logging system
        stop_detection_logging()
        
        super().destroy()
