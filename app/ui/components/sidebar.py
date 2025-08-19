import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_nav):
        super().__init__(master, width=200, corner_radius=10)
        self.pack_propagate(False)
        self.on_nav = on_nav
        
        # Sidebar title
        title = ctk.CTkLabel(
            self, 
            text="Navigation", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=(20, 10), padx=20)
        
        # Navigation buttons
        nav_items = [
            ("🏠 Dashboard", "dashboard"),
            ("🚗 License Plates", "license_plates")
        ]
        
        for text, key in nav_items:
            btn = ctk.CTkButton(
                self,
                text=text,
                command=lambda k=key: self.on_nav(k),
                width=160,
                height=40,
                font=ctk.CTkFont(size=12),
                corner_radius=8
            )
            btn.pack(padx=20, pady=5, fill="x")
