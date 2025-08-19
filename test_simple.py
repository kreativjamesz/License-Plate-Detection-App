"""
Simple test to verify if the app works without database
"""

import customtkinter as ctk

def test_basic_ui():
    """Test basic UI without database"""
    print("🔍 Testing basic UI...")
    
    root = ctk.CTk()
    root.title("Basic UI Test")
    root.geometry("400x300")
    
    label = ctk.CTkLabel(root, text="✅ Basic UI Working!", font=ctk.CTkFont(size=20))
    label.pack(expand=True)
    
    def close_app():
        print("✅ Basic UI test completed!")
        root.destroy()
    
    button = ctk.CTkButton(root, text="Close", command=close_app)
    button.pack(pady=20)
    
    # Auto-close after 3 seconds
    root.after(3000, close_app)
    root.mainloop()

if __name__ == "__main__":
    print("🧪 Running basic UI test...")
    test_basic_ui()
    print("🎉 Test completed!")
