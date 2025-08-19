import customtkinter as ctk
from tkinter import messagebox
from app.services.auth_service import register_user
from app.ui.widget.gradient_button import GradientButton

class RegisterPage(ctk.CTkFrame):
    def __init__(self, master, on_success, on_back):
        super().__init__(master)
        self.on_success = on_success
        self.on_back = on_back
        self._build()

    def _build(self):
        # Main container with padding
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Center container
        center_frame = ctk.CTkFrame(self, corner_radius=20)
        center_frame.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        center_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            center_frame, 
            text="🎓 Create Account", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(40, 10), sticky="ew")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            center_frame, 
            text="Join the School Face Attendance System", 
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 30), sticky="ew")
        
        # Form container
        form_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        form_frame.grid(row=2, column=0, padx=40, pady=20, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        # Username field
        username_label = ctk.CTkLabel(
            form_frame, 
            text="👤 Username", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        username_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.username = ctk.CTkEntry(
            form_frame, 
            placeholder_text="Enter your username",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.username.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Password field
        password_label = ctk.CTkLabel(
            form_frame, 
            text="🔒 Password", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        password_label.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        
        self.password = ctk.CTkEntry(
            form_frame, 
            placeholder_text="Enter your password",
            show="*",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.password.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        
        # Confirm Password field
        confirm_label = ctk.CTkLabel(
            form_frame, 
            text="🔐 Confirm Password", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        confirm_label.grid(row=4, column=0, sticky="ew", pady=(0, 5))
        
        self.confirm_password = ctk.CTkEntry(
            form_frame, 
            placeholder_text="Confirm your password",
            show="*",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.confirm_password.grid(row=5, column=0, sticky="ew", pady=(0, 30))
        
        # Buttons container
        button_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=40, pady=(0, 40), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Back button
        back_btn = ctk.CTkButton(
            button_frame,
            text="← Back",
            command=self.on_back,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        back_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # Register button
        try:
            register_btn = GradientButton(
                button_frame,
                text="Create Account 🚀",
                command=self._do_register,
                width=200,
                height=45,
                corner_radius=25
            )
            register_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        except:
            # Fallback to regular button if gradient button fails
            register_btn = ctk.CTkButton(
                button_frame,
                text="Create Account 🚀",
                command=self._do_register,
                height=45,
                font=ctk.CTkFont(size=14, weight="bold"),
                corner_radius=25
            )
            register_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        
        # Bind Enter key to register
        self.username.bind('<Return>', lambda e: self._do_register())
        self.password.bind('<Return>', lambda e: self._do_register())
        self.confirm_password.bind('<Return>', lambda e: self._do_register())
        
        # Focus on username field
        self.after(100, lambda: self.username.focus())

    def _do_register(self):
        username = self.username.get().strip()
        password = self.password.get().strip()
        confirm = self.confirm_password.get().strip()
        
        # Validation
        if not username or not password:
            messagebox.showerror("Registration Error", "Please fill in all fields.")
            return
            
        if len(username) < 3:
            messagebox.showerror("Registration Error", "Username must be at least 3 characters long.")
            return
            
        if len(password) < 6:
            messagebox.showerror("Registration Error", "Password must be at least 6 characters long.")
            return
            
        if password != confirm:
            messagebox.showerror("Registration Error", "Passwords do not match!")
            return
        
        # Attempt registration
        ok, msg = register_user(username, password)
        if ok:
            messagebox.showinfo("Registration Successful", f"Welcome {username}! Your account has been created successfully.")
            # Clear form
            self.username.delete(0, 'end')
            self.password.delete(0, 'end')
            self.confirm_password.delete(0, 'end')
            self.on_success()
        else:
            messagebox.showerror("Registration Failed", msg)
