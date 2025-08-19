import customtkinter as ctk
from datetime import datetime
from app.services.license_plate_service import LicensePlateService
from app.services.detection_logger import detection_logger
import threading

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.license_plate_service = LicensePlateService()
        
        try:
            self._build()
        except Exception as e:
            print(f"❌ Error building dashboard: {e}")
            self._build_fallback()
    
    def _build(self):
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header section
        header_frame = ctk.CTkFrame(self, corner_radius=15)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Welcome title
        welcome_label = ctk.CTkLabel(
            header_frame,
            text="📊 License Plate Detection Dashboard",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        welcome_label.grid(row=0, column=0, sticky="w", padx=30, pady=20)
        
        # Current date/time
        current_time = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        time_label = ctk.CTkLabel(
            header_frame,
            text=current_time,
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        time_label.grid(row=0, column=1, sticky="e", padx=30, pady=20)
        
        # Stats cards container
        stats_frame = ctk.CTkFrame(self, corner_radius=15)
        stats_frame.grid(row=1, column=0, sticky="nsew")
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        stats_frame.grid_rowconfigure((0, 1), weight=1)
        
        # Load license plate stats data
        self._load_and_display_license_plate_stats(stats_frame)
        
        # Recent detections section
        activity_frame = ctk.CTkFrame(stats_frame, corner_radius=10)
        activity_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=20, pady=20)
        activity_frame.grid_columnconfigure(0, weight=1)
        
        activity_title = ctk.CTkLabel(
            activity_frame,
            text="📋 Recent License Plate Detections",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        activity_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        # Load recent detections
        self._load_recent_detections(activity_frame)
    
    def _create_stat_card(self, parent, title, value, subtitle, row, col):
        """Create a statistics card"""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=row, column=col, sticky="nsew", padx=20, pady=20)
        card.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 5))
        
        # Value
        value_label = ctk.CTkLabel(
            card,
            text=str(value),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#1f538d", "#4a9eff")
        )
        value_label.grid(row=1, column=0, pady=5)
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        subtitle_label.grid(row=2, column=0, pady=(5, 20))
    
    def _load_and_display_license_plate_stats(self, parent):
        """Load and display license plate statistics"""
        # Create stats immediately with loading text
        self._create_stat_card(parent, "🚗 Total Plates", "Loading...", "All detections", 0, 0)
        self._create_stat_card(parent, "📅 Today", "Loading...", "Today's detections", 0, 1)
        self._create_stat_card(parent, "✅ Verified", "Loading...", "Verified plates", 0, 2)
        
        # Store parent reference for updating
        self.dashboard_stats_parent = parent
        
        def load_stats():
            try:
                # Load license plate stats from database
                stats = self.license_plate_service.get_plates_count()
                total_plates = stats.get("total", 0)
                verified_plates = stats.get("verified", 0)
                
                # Get today's detections from database
                today_db_detections = len(self.license_plate_service.get_todays_detections())
                
                # Get today's logged detections (real-time from log files)
                today_log_detections = detection_logger.get_today_detections_count()
                
                # Update UI in main thread
                self.after(0, lambda: self._update_dashboard_stats_display(
                    total_plates, today_db_detections, verified_plates, today_log_detections
                ))
                
            except Exception as e:
                print(f"❌ Error loading license plate stats: {e}")
                # Show error stats
                self.after(0, lambda: self._update_dashboard_stats_display(
                    "Error", "Error", "Error"
                ))
        
        thread = threading.Thread(target=load_stats, daemon=True)
        thread.start()
    
    def _update_dashboard_stats_display(self, total_plates, today_db_detections, verified_plates, today_log_detections=0):
        """Update existing dashboard stats display"""
        # Clear existing stats widgets
        if hasattr(self, 'dashboard_stats_parent') and self.dashboard_stats_parent.winfo_exists():
            for widget in self.dashboard_stats_parent.winfo_children():
                # Only remove stat cards (not activity section)
                if widget.grid_info().get('row') == 0:
                    widget.destroy()
            
            # Recreate with new data - show both database and log stats
            self._create_stat_card(self.dashboard_stats_parent, "🚗 Total Plates", total_plates, "In database", 0, 0)
            self._create_stat_card(self.dashboard_stats_parent, "📅 DB Today", today_db_detections, "Saved to database", 0, 1) 
            self._create_stat_card(self.dashboard_stats_parent, "📝 Logged Today", today_log_detections, "Fast log entries", 0, 2)
    
    def _load_recent_detections(self, parent):
        """Load and display recent license plate detections"""
        # Initial loading message
        loading_label = ctk.CTkLabel(
            parent,
            text="Loading recent detections...",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        loading_label.grid(row=1, column=0, sticky="w", padx=20, pady=5)
        
        def load_detections():
            try:
                # Get recent plates (last 5)
                recent_plates = self.license_plate_service.get_plates_for_table()[:5]
                
                # Update UI in main thread
                self.after(0, lambda: self._display_recent_detections(parent, recent_plates))
                
            except Exception as e:
                print(f"❌ Error loading recent detections: {e}")
                self.after(0, lambda: self._display_recent_detections(parent, []))
        
        thread = threading.Thread(target=load_detections, daemon=True)
        thread.start()
    
    def _display_recent_detections(self, parent, recent_plates):
        """Display recent detections in the activity frame"""
        # Clear loading message
        for widget in parent.winfo_children():
            if widget.grid_info().get('row') > 0:
                widget.destroy()
        
        if not recent_plates:
            no_data_label = ctk.CTkLabel(
                parent,
                text="🔍 No license plate detections yet.\nStart the camera to begin detecting plates!",
                font=ctk.CTkFont(size=14),
                text_color=("gray60", "gray40"),
                justify="center"
            )
            no_data_label.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
            return
        
        # Display recent detections
        for i, plate_data in enumerate(recent_plates):
            if i >= 5:  # Limit to 5 recent detections
                break
            
            plate_id, plate_text, date_detected, time_detected, location, status = plate_data
            
            activity_text = f"🚗 Detected plate: {plate_text} at {time_detected} - {status}"
            
            activity_label = ctk.CTkLabel(
                parent,
                text=activity_text,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            activity_label.grid(row=i+1, column=0, sticky="ew", padx=20, pady=5)
        
        # Add a "View All" link
        view_all_label = ctk.CTkLabel(
            parent,
            text="👉 Click 'License Plates' to view all detections",
            font=ctk.CTkFont(size=12),
            text_color=("#1f538d", "#4a9eff"),
            anchor="w"
        )
        view_all_label.grid(row=len(recent_plates)+1, column=0, sticky="ew", padx=20, pady=(10, 20))
    
    def _build_fallback(self):
        """Build fallback dashboard when main build fails"""
        try:
            error_label = ctk.CTkLabel(
                self,
                text="⚠️ Dashboard Error\n\nUnable to load dashboard properly.\nPlease check your setup.",
                font=ctk.CTkFont(size=16),
                text_color=("gray60", "gray40"),
                justify="center"
            )
            error_label.pack(expand=True, fill="both", padx=50, pady=50)
        except Exception as e:
            print(f"❌ Error creating fallback dashboard: {e}")