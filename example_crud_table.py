"""
Example of using the new CRUD-enabled DataTable
Run this to test the new functionality
"""

import customtkinter as ctk
from app.ui.widget.data_table import DataTable
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TestCRUDApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("CRUD DataTable Test")
        self.geometry("900x600")
        
        # Sample data
        self.sample_data = [
            ["1", "John Doe", "BSIT", "A1"],
            ["2", "Jane Smith", "BSCS", "B2"],
            ["3", "Bob Johnson", "BSECE", "C3"],
            ["4", "Alice Brown", "BSIT", "A2"],
            ["5", "Charlie Wilson", "BSCS", "B1"]
        ]
        
        # Create CRUD table
        self.table = DataTable(
            self,
            headers=["ID", "Full Name", "Course", "Section"],
            data=self.sample_data.copy(),
            on_add=self.add_student,
            on_edit=self.edit_student,
            on_delete=self.delete_student,
            on_refresh=self.refresh_data,
            searchable=True,
            show_toolbar=True
        )
        self.table.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready - Try the CRUD buttons above!",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(0, 10))
    
    def add_student(self):
        """Add a new student"""
        # Simple dialog for testing
        dialog = ctk.CTkInputDialog(
            text="Enter student name:",
            title="Add Student"
        )
        name = dialog.get_input()
        
        if name:
            # Generate new ID
            new_id = str(len(self.sample_data) + 1)
            new_row = [new_id, name, "BSIT", "A1"]
            
            # Add to data
            self.sample_data.append(new_row)
            
            # Update table
            self.table.update_data(data=self.sample_data.copy())
            
            self.status_label.configure(text=f"✅ Added student: {name}")
    
    def edit_student(self, row_data):
        """Edit selected student"""
        if not row_data:
            return
        
        current_name = row_data[1]
        dialog = ctk.CTkInputDialog(
            text=f"Edit student name (current: {current_name}):",
            title="Edit Student"
        )
        new_name = dialog.get_input()
        
        if new_name:
            # Find and update in sample_data
            student_id = row_data[0]
            for i, student in enumerate(self.sample_data):
                if student[0] == student_id:
                    self.sample_data[i][1] = new_name
                    break
            
            # Update table
            self.table.update_data(data=self.sample_data.copy())
            
            self.status_label.configure(text=f"✏️ Updated student: {new_name}")
    
    def delete_student(self, row_data):
        """Delete selected student"""
        if not row_data:
            return
        
        name = row_data[1]
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{name}'?"
        )
        
        if result:
            # Remove from sample_data
            student_id = row_data[0]
            self.sample_data = [s for s in self.sample_data if s[0] != student_id]
            
            # Update table
            self.table.update_data(data=self.sample_data.copy())
            
            self.status_label.configure(text=f"🗑️ Deleted student: {name}")
    
    def refresh_data(self):
        """Refresh table data"""
        # Simulate loading fresh data
        self.table.update_data(data=self.sample_data.copy())
        self.status_label.configure(text="🔄 Data refreshed!")

if __name__ == "__main__":
    app = TestCRUDApp()
    app.mainloop()
