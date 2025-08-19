import customtkinter as ctk
from app.ui.components.navbar import Navbar
from app.ui.components.sidebar import Sidebar

class Shell(ctk.CTkFrame):
    def __init__(self, master, on_nav_change):
        super().__init__(master, corner_radius=15)
        self.pack(fill="both", expand=True)
        self.on_nav_change = on_nav_change

        # Navbar
        self.navbar = Navbar(self, title="🎓 School Attendance System")
        self.navbar.pack(pady=10)
        
        # Body container
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Sidebar
        self.sidebar = Sidebar(self.body, on_nav=self.on_nav_change)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))

        # Content area
        self.content = ctk.CTkFrame(self.body, corner_radius=10)
        self.content.pack(side="left", fill="both", expand=True)
        
        # Store created pages (ChatGPT approach!)
        self.pages = {}
        self.current_page = None

    def set_content(self, page_name: str, widget_factory=None):
        """Set content using ChatGPT's approach - cache pages instead of destroying"""
        try:
            # Hide current page if exists
            if self.current_page and self.current_page in self.pages:
                self.pages[self.current_page].pack_forget()
            
            # Create page if doesn't exist
            if page_name not in self.pages:
                if widget_factory:
                    widget = widget_factory()
                    if widget and hasattr(widget, 'pack'):
                        self.pages[page_name] = widget
                        print(f"✅ Created and cached page: {page_name}")
                    else:
                        raise ValueError(f"Invalid widget factory for {page_name}")
                else:
                    raise ValueError(f"No widget factory provided for {page_name}")
            
            # Show the requested page
            self.pages[page_name].pack(fill="both", expand=True, padx=20, pady=20)
            self.current_page = page_name
            print(f"✅ Switched to page: {page_name}")
            
        except Exception as e:
            print(f"⚠️ Error setting content: {e}")
            self._create_fallback_content(str(e))
    
    def _create_fallback_content(self, error_msg: str):
        """Create fallback content when widget creation fails"""
        try:
            # Clear any existing content first
            for widget in self.content.winfo_children():
                widget.pack_forget()
                
            fallback = ctk.CTkLabel(
                self.content, 
                text=f"⚠️ Error loading page content\n\nError: {error_msg}\n\nPlease try navigating again",
                font=ctk.CTkFont(size=14),
                text_color=("gray60", "gray40"),
                justify="center"
            )
            fallback.pack(fill="both", expand=True, padx=20, pady=20)
        except Exception as fallback_error:
            print(f"❌ Critical error creating fallback: {fallback_error}")
    
    def clear_all_pages(self):
        """Clear all cached pages - useful for refresh/logout"""
        try:
            for page_name, page_widget in self.pages.items():
                try:
                    page_widget.pack_forget()
                    page_widget.destroy()
                except:
                    pass
            self.pages.clear()
            self.current_page = None
            print("🗑️ Cleared all cached pages")
        except Exception as e:
            print(f"⚠️ Error clearing pages: {e}")
