import customtkinter as ctk


class HomePage(ctk.CTkFrame):
    def __init__(self, master, on_login, on_register):
        super().__init__(master, corner_radius=15)
        self.on_login = on_login
        self.on_register = on_register
        self._build()

    def _build(self):
        # Welcome title
        title = ctk.CTkLabel(
            self,
            text="Welcome to School Attendance System",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=(50, 20))

        # Subtitle
        subtitle = ctk.CTkLabel(
            self,
            text="Secure face-based authentication for students",
            font=ctk.CTkFont(size=14),
        )
        subtitle.pack(pady=(0, 40))

        # Button container
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        # Login button with your first color
        login_btn = ctk.CTkButton(
            button_frame,
            text="🔑 Login",
            command=self.on_login,
            width=180,
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            fg_color="#8972f5",  # Your purple color
            hover_color="#6061dd",  # Your blue color on hover
        )
        login_btn.pack(side="left", padx=15)

        # Register button with your second color
        register_btn = ctk.CTkButton(
            button_frame,
            text="✨ Register",
            command=self.on_register,
            width=180,
            height=55,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            fg_color="#6061dd",  # Your blue color
            hover_color="#8972f5",  # Your purple color on hover
        )
        register_btn.pack(side="left", padx=15)
