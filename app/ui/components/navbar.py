import customtkinter as ctk

class Navbar(ctk.CTkFrame):
    def __init__(self, master, title="School App"):
        super().__init__(master, height=60, corner_radius=10)
        self.pack(fill="x", padx=10, pady=(0,10))
        
        # Title label
        title_label = ctk.CTkLabel(
            self, 
            text=title, 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
