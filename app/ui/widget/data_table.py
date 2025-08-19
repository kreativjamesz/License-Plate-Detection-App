"""
DataTable - Reusable table widget using tksheet
Integrates with our DataService for displaying database data
"""

import customtkinter as ctk
try:
    from tksheet import Sheet
    TKSHEET_AVAILABLE = True
except ImportError:
    TKSHEET_AVAILABLE = False
    print("⚠️ tksheet not available. Install with: pip install tksheet")

from typing import List, Dict, Callable, Optional
import threading
from app.services.pagination import PaginationParams, PaginationResult

class DataTable(ctk.CTkFrame):
    """
    Reusable table widget with built-in CRUD toolbar
    Uses tksheet for Excel-like functionality with dark theme
    """
    
    def __init__(
        self, 
        master,
        headers: List[str] = None,
        data: List[List] = None,
        height: int = 400,
        width: int = 800,
        font_size: int = 11,
        header_font_size: int = 12,
        on_select: Callable = None,
        on_double_click: Callable = None,
        on_add: Optional[Callable] = None,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        on_refresh: Optional[Callable] = None,
        searchable: bool = True,
        show_toolbar: bool = True,
        show_pagination: bool = False,
        pagination_result: PaginationResult = None,
        on_page_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.headers = headers or []
        self.data = data or []
        self.font_size = font_size
        self.header_font_size = header_font_size
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.on_add = on_add
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_refresh = on_refresh
        self.searchable = searchable
        self.show_toolbar = show_toolbar
        self.show_pagination = show_pagination
        self.pagination_result = pagination_result
        self.on_page_change = on_page_change
        self.height = height
        self.width = width
        
        self.sheet = None
        self.search_entry = None
        self.selected_row_data = None
        
        # Build the complete widget
        self._build_widget()
    
    def _build_widget(self):
        """Build the complete widget with toolbar, table, and pagination"""
        # Configure grid - adjust based on what we're showing
        self.grid_columnconfigure(0, weight=1)
        
        current_row = 0
        
        # Create toolbar if requested
        if self.show_toolbar:
            self._create_toolbar()
            current_row += 1
        
        # Table row expands
        self.grid_rowconfigure(current_row, weight=1)
        
        # Create table container
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=current_row, column=0, sticky="nsew", padx=5, pady=5)
        current_row += 1
        
        # Create the actual table
        self._create_table()
        
        # Create pagination if requested
        if self.show_pagination:
            self._create_pagination()
            current_row += 1
    
    def _create_toolbar(self):
        """Create CRUD toolbar (ChatGPT approach)"""
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(2, weight=1)  # Center spacer
        
        # Left side buttons
        left_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")
        
        # Add button
        if self.on_add:
            add_btn = ctk.CTkButton(
                left_frame,
                text="➕ Add",
                command=lambda: self._safe_call(self.on_add),
                width=80,
                height=32,
                font=ctk.CTkFont(size=12)
            )
            add_btn.pack(side="left", padx=2)
        
        # Edit button
        if self.on_edit:
            edit_btn = ctk.CTkButton(
                left_frame,
                text="✏️ Edit",
                command=lambda: self._safe_call(self._edit_selected),
                width=80,
                height=32,
                font=ctk.CTkFont(size=12)
            )
            edit_btn.pack(side="left", padx=2)
        
        # Delete button
        if self.on_delete:
            delete_btn = ctk.CTkButton(
                left_frame,
                text="🗑️ Delete",
                command=lambda: self._safe_call(self._delete_selected),
                width=90,
                height=32,
                font=ctk.CTkFont(size=12),
                fg_color="#ef4444",
                hover_color="#dc2626"
            )
            delete_btn.pack(side="left", padx=2)
        
        # Refresh button
        if self.on_refresh:
            refresh_btn = ctk.CTkButton(
                left_frame,
                text="🔄 Refresh",
                command=lambda: self._safe_call(self.on_refresh),
                width=90,
                height=32,
                font=ctk.CTkFont(size=12),
                fg_color="#8b5cf6",
                hover_color="#7c3aed"
            )
            refresh_btn.pack(side="left", padx=2)
        
        # Right side - Search
        if self.searchable:
            right_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
            right_frame.grid(row=0, column=1, sticky="e")
            
            # Search entry
            self.search_entry = ctk.CTkEntry(
                right_frame,
                placeholder_text="Search table...",
                width=200,
                height=32,
                font=ctk.CTkFont(size=12)
            )
            self.search_entry.pack(side="left", padx=2)
            self.search_entry.bind('<KeyRelease>', self._on_search_change)
            
            # Search button
            search_btn = ctk.CTkButton(
                right_frame,
                text="🔍",
                command=self._search,
                width=40,
                height=32,
                font=ctk.CTkFont(size=12)
            )
            search_btn.pack(side="left", padx=2)
    
    def _create_pagination(self):
        """Create pagination controls"""
        if not self.pagination_result:
            return
        
        # Find the correct row for pagination (after table)
        pagination_row = 2 if self.show_toolbar else 1
        
        pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        pagination_frame.grid(row=pagination_row, column=0, sticky="ew", padx=5, pady=5)
        pagination_frame.grid_columnconfigure(1, weight=1)  # Center spacer
        
        # Left side - Page info
        page_info_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        page_info_frame.grid(row=0, column=0, sticky="w")
        
        page_info_label = ctk.CTkLabel(
            page_info_frame,
            text=self.pagination_result.get_page_info(),
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40")
        )
        page_info_label.pack(side="left", padx=5)
        
        # Right side - Navigation controls
        nav_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        nav_frame.grid(row=0, column=2, sticky="e")
        
        # First button
        if self.pagination_result.page > 1:
            first_btn = ctk.CTkButton(
                nav_frame,
                text="⏮️",
                command=lambda: self._change_page(1),
                width=30,
                height=30,
                font=ctk.CTkFont(size=12)
            )
            first_btn.pack(side="left", padx=1)
        
        # Previous button
        if self.pagination_result.has_prev:
            prev_btn = ctk.CTkButton(
                nav_frame,
                text="◀️",
                command=lambda: self._change_page(self.pagination_result.page - 1),
                width=30,
                height=30,
                font=ctk.CTkFont(size=12)
            )
            prev_btn.pack(side="left", padx=1)
        
        # Page numbers
        page_numbers = self.pagination_result.get_page_numbers()
        for page_num in page_numbers:
            if page_num == self.pagination_result.page:
                # Current page (highlighted)
                page_btn = ctk.CTkButton(
                    nav_frame,
                    text=str(page_num),
                    command=lambda p=page_num: self._change_page(p),
                    width=35,
                    height=30,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color="#1f538d",
                    hover_color="#4a9eff"
                )
            else:
                # Other pages
                page_btn = ctk.CTkButton(
                    nav_frame,
                    text=str(page_num),
                    command=lambda p=page_num: self._change_page(p),
                    width=35,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color="transparent",
                    text_color=("gray60", "gray40"),
                    hover_color=("gray80", "gray20")
                )
            page_btn.pack(side="left", padx=1)
        
        # Next button
        if self.pagination_result.has_next:
            next_btn = ctk.CTkButton(
                nav_frame,
                text="▶️",
                command=lambda: self._change_page(self.pagination_result.page + 1),
                width=30,
                height=30,
                font=ctk.CTkFont(size=12)
            )
            next_btn.pack(side="left", padx=1)
        
        # Last button
        if self.pagination_result.page < self.pagination_result.total_pages:
            last_btn = ctk.CTkButton(
                nav_frame,
                text="⏭️",
                command=lambda: self._change_page(self.pagination_result.total_pages),
                width=30,
                height=30,
                font=ctk.CTkFont(size=12)
            )
            last_btn.pack(side="left", padx=1)
        
        # Items per page selector
        per_page_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        per_page_frame.grid(row=0, column=3, sticky="e", padx=(10, 0))
        
        per_page_label = ctk.CTkLabel(
            per_page_frame,
            text="Per page:",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40")
        )
        per_page_label.pack(side="left", padx=(0, 5))
        
        per_page_values = ["10", "25", "50", "100"]
        current_limit = str(self.pagination_result.limit)
        
        self.per_page_combo = ctk.CTkComboBox(
            per_page_frame,
            values=per_page_values,
            command=self._change_per_page,
            width=70,
            height=30,
            font=ctk.CTkFont(size=11)
        )
        self.per_page_combo.set(current_limit)
        self.per_page_combo.pack(side="left")
    
    def _change_page(self, page: int):
        """Handle page change"""
        if self.on_page_change:
            self.on_page_change(page)
    
    def _change_per_page(self, limit_str: str):
        """Handle per page change"""
        if self.on_page_change:
            try:
                limit = int(limit_str)
                # Call page change with page 1 and new limit
                self.on_page_change(1, limit)
            except ValueError:
                print(f"⚠️ Invalid limit: {limit_str}")
    
    def update_pagination(self, pagination_result: PaginationResult):
        """Update pagination with new result"""
        self.pagination_result = pagination_result
        
        # Rebuild pagination if it's showing
        if self.show_pagination:
            # Remove existing pagination
            pagination_row = 2 if self.show_toolbar else 1
            for widget in self.grid_slaves(row=pagination_row):
                widget.destroy()
            
            # Recreate pagination
            self._create_pagination()
    
    def _safe_call(self, func):
        """Safely call a callback function"""
        try:
            if func:
                func()
        except Exception as e:
            print(f"⚠️ Callback error: {e}")
    
    def _edit_selected(self):
        """Edit the selected row"""
        row = self.get_selected_row()
        if row and self.on_edit:
            self.on_edit(row)
        elif not row:
            print("⚠️ No row selected for editing")
    
    def _delete_selected(self):
        """Delete the selected row"""
        row = self.get_selected_row()
        if row and self.on_delete:
            self.on_delete(row)
        elif not row:
            print("⚠️ No row selected for deletion")
    
    def _search(self):
        """Perform search"""
        if not self.search_entry:
            return
        
        term = self.search_entry.get().strip()
        if not term:
            print("⚠️ Enter search term")
            return
        
        matches = self.search_and_highlight(term)
        print(f"🔍 Found {len(matches)} matching rows")
    
    def _on_search_change(self, event):
        """Handle search as user types"""
        if not self.search_entry:
            return
        
        term = self.search_entry.get().strip()
        if len(term) >= 2:  # Start searching after 2 characters
            self.search_and_highlight(term)
        elif len(term) == 0:
            # Clear search - show all data
            self.update_data(data=self.data)
    
    def _create_table(self):
        """Create the table widget"""
        if not TKSHEET_AVAILABLE:
            # Fallback to dark-styled Treeview if tksheet not available
            self._create_dark_treeview()
            return
        
        # Configure grid for table frame
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        
        # Create sheet widget with dark styling
        self.sheet = Sheet(
            self.table_frame,  # Use table_frame as parent
            headers=self.headers,
            data=self.data,
            height=self.height,
            width=self.width,
            show_table=True,
            show_top_left=True,
            show_row_index=True,
            show_header=True,
            empty_horizontal=0,
            empty_vertical=0
        )
        
        # Apply dark theme to tksheet
        self._apply_dark_theme_to_sheet()
        
        # Configure sheet appearance
        self.sheet.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Enable features
        self.sheet.enable_bindings([
            "single_select",
            "double_click_column_resize",
            "column_select",
            "row_select",
            "column_width_resize",
            "double_click_row_resize",
            "right_click_popup_menu",
            "copy",
            "select_all"
        ])
        
        # Bind events
        if self.on_select:
            self.sheet.bind("<<SheetSelect>>", self._on_sheet_select)
        
        if self.on_double_click:
            self.sheet.bind("<Double-Button-1>", self._on_sheet_double_click)
    
    def _apply_dark_theme_to_sheet(self):
        """Apply dark theme styling to tksheet"""
        if not self.sheet:
            return
            
        try:
            # Dark theme colors
            dark_bg = "#2b2b2b"
            dark_fg = "#ffffff"
            header_bg = "#1f538d"
            header_fg = "#ffffff"
            selected_bg = "#4a9eff"
            grid_color = "#404040"
            
            # Apply dark theme
            self.sheet.set_options(
                table_bg=dark_bg,
                table_fg=dark_fg,
                table_selected_cells_bg=selected_bg,
                table_selected_cells_fg="#ffffff",
                index_bg=dark_bg,
                index_fg=dark_fg,
                header_bg=header_bg,
                header_fg=header_fg,
                header_selected_cells_bg="#3b82f6",
                header_selected_cells_fg="#ffffff",
                top_left_bg=header_bg,
                top_left_fg=header_fg,
                table_grid_fg=grid_color,
                header_grid_fg=grid_color,
                index_grid_fg=grid_color,
                selected_rows_bg="#1e40af",
                selected_rows_fg="#ffffff",
                selected_columns_bg="#1e40af",
                selected_columns_fg="#ffffff"
            )
            
            print("✅ Applied dark theme to tksheet")
            
        except Exception as e:
            print(f"⚠️ Could not apply dark theme to tksheet: {e}")
    
    def _create_dark_treeview(self):
        """Create dark-styled Treeview as fallback"""
        try:
            from tkinter import ttk
            
            # Configure grid for table frame
            self.table_frame.grid_columnconfigure(0, weight=1)
            self.table_frame.grid_rowconfigure(0, weight=1)
            
            # Setup dark Treeview style
            style = ttk.Style()
            style.theme_use("default")
            
            # Dark mode styling with custom font sizes
            style.configure(
                "Dark.Treeview",
                background="#2b2b2b",
                foreground="#ffffff",
                fieldbackground="#2b2b2b",
                rowheight=35,  # More breathing room
                font=("Arial", self.font_size)
            )
            style.configure(
                "Dark.Treeview.Heading",
                font=("Arial", self.header_font_size, "bold"),
                background="#1f538d",
                foreground="#ffffff",
                relief="flat"
            )
            style.map(
                "Dark.Treeview",
                background=[("selected", "#4a9eff")],
                foreground=[("selected", "#ffffff")]
            )
            
            # Create Treeview
            if self.headers:
                columns = [f"col{i}" for i in range(len(self.headers))]
            else:
                columns = ["col0"]
            
            self.tree = ttk.Treeview(
                self.table_frame,  # Use table_frame as parent
                columns=columns,
                show="headings",
                style="Dark.Treeview"
            )
            
            # Set up headers
            if self.headers:
                for i, header in enumerate(self.headers):
                    col_id = f"col{i}"
                    self.tree.heading(col_id, text=header)
                    self.tree.column(col_id, width=120, anchor="center")
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=scrollbar.set)
            
            # Grid the widgets
            self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
            scrollbar.grid(row=0, column=1, sticky="ns", pady=10, padx=(0, 10))
            
            # Add initial data
            self._populate_treeview()
            
            # Bind events
            if self.on_select:
                self.tree.bind("<<TreeviewSelect>>", self._on_treeview_select)
            if self.on_double_click:
                self.tree.bind("<Double-1>", self._on_treeview_double_click)
            
            # Bind click events for action column buttons
            self.tree.bind("<Button-1>", self._on_treeview_click)
                
            print("✅ Created dark-styled Treeview fallback")
            
        except Exception as e:
            print(f"❌ Error creating dark Treeview: {e}")
            self._create_fallback_table()
    
    def _populate_treeview(self):
        """Populate Treeview with data"""
        if not hasattr(self, 'tree'):
            return
            
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Add data rows
            for row_data in self.data:
                self.tree.insert("", "end", values=row_data)
                
        except Exception as e:
            print(f"❌ Error populating Treeview: {e}")
    
    def _on_treeview_select(self, event):
        """Handle Treeview selection"""
        if not self.on_select or not hasattr(self, 'tree'):
            return
            
        try:
            selection = self.tree.selection()
            if selection:
                item = self.tree.item(selection[0])
                values = item['values']
                if values:
                    self.on_select(list(values))
        except Exception as e:
            print(f"❌ Treeview selection error: {e}")
    
    def _on_treeview_double_click(self, event):
        """Handle Treeview double click"""
        if not self.on_double_click or not hasattr(self, 'tree'):
            return
            
        try:
            selection = self.tree.selection()
            if selection:
                item = self.tree.item(selection[0])
                values = item['values']
                if values:
                    self.on_double_click(list(values))
        except Exception as e:
            print(f"❌ Treeview double click error: {e}")
    
    def _on_treeview_click(self, event):
        """Handle Treeview click - detect action column clicks"""
        if not hasattr(self, 'tree'):
            return
            
        try:
            # Identify which item was clicked
            item = self.tree.identify('item', event.x, event.y)
            column = self.tree.identify('column', event.x, event.y)
            
            if not item or not column:
                return
            
            # Get row data
            item_data = self.tree.item(item)
            values = item_data['values']
            
            if not values:
                return
                
            # Check if clicked on Actions column (last column)
            try:
                col_index = int(column) - 1  # Column numbers start at 1
                if col_index == len(self.headers) - 1 and "Actions" in self.headers:  # Last column is Actions
                    row_data = list(values)[:-1]  # Exclude Actions column from row data
                    
                    # Determine click position within the column to detect edit vs delete
                    column_x = event.x
                    # Simple heuristic: left half = edit, right half = delete
                    bbox = self.tree.bbox(item, column)
                    if bbox:
                        col_width = bbox[2]
                        relative_x = column_x - bbox[0]
                        
                        if relative_x < col_width / 2:  # Left half - Edit
                            if self.on_edit:
                                print(f"✏️ Edit clicked for row: {row_data[0] if row_data else 'Unknown'}")
                                self.on_edit(row_data)
                        else:  # Right half - Delete
                            if self.on_delete:
                                print(f"🗑️ Delete clicked for row: {row_data[0] if row_data else 'Unknown'}")
                                self.on_delete(row_data)
            except (ValueError, IndexError) as e:
                print(f"⚠️ Action column click error: {e}")
                
        except Exception as e:
            print(f"❌ Treeview click error: {e}")
    
    def _create_fallback_table(self):
        """Create basic table if tksheet not available"""
        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create header row
        if self.headers:
            for col, header in enumerate(self.headers):
                header_label = ctk.CTkLabel(
                    self.scrollable_frame,
                    text=header,
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                header_label.grid(row=0, column=col, padx=5, pady=5, sticky="ew")
        
        # Create data rows
        for row_idx, row_data in enumerate(self.data, start=1):
            for col_idx, cell_data in enumerate(row_data):
                cell_label = ctk.CTkLabel(
                    self.scrollable_frame,
                    text=str(cell_data),
                    font=ctk.CTkFont(size=12)
                )
                cell_label.grid(row=row_idx, column=col_idx, padx=5, pady=2, sticky="ew")
        
        # Configure column weights
        for col in range(len(self.headers)):
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
    
    def _on_sheet_select(self, event):
        """Handle sheet selection"""
        if self.on_select and self.sheet:
            try:
                selected = self.sheet.get_currently_selected()
                if selected:
                    row = selected.row
                    if row is not None and row < len(self.data):
                        self.on_select(self.data[row])
            except Exception as e:
                print(f"Selection error: {e}")
    
    def _on_sheet_double_click(self, event):
        """Handle sheet double click"""
        if self.on_double_click and self.sheet:
            try:
                selected = self.sheet.get_currently_selected()
                if selected:
                    row = selected.row
                    if row is not None and row < len(self.data):
                        self.on_double_click(self.data[row])
            except Exception as e:
                print(f"Double click error: {e}")
    
    def update_data(self, headers: List[str] = None, data: List[List] = None):
        """Update table data"""
        if headers:
            self.headers = headers
        if data:
            self.data = data
        
        if TKSHEET_AVAILABLE and self.sheet:
            # Update tksheet
            self.sheet.set_sheet_data(data=self.data)
            if headers:
                self.sheet.headers(headers)
            self.sheet.refresh()
        elif hasattr(self, 'tree'):
            # Update Treeview
            self._populate_treeview()
        else:
            # Recreate fallback table
            if hasattr(self, 'scrollable_frame'):
                for widget in self.scrollable_frame.winfo_children():
                    widget.destroy()
                self._create_fallback_table()
    
    def get_selected_row(self):
        """Get currently selected row data"""
        if TKSHEET_AVAILABLE and self.sheet:
            try:
                selected = self.sheet.get_currently_selected()
                if selected:
                    row = selected.row
                    if row is not None and row < len(self.data):
                        return self.data[row]
            except Exception as e:
                print(f"Get selection error: {e}")
        return None
    
    def clear_data(self):
        """Clear all table data"""
        self.data = []
        if TKSHEET_AVAILABLE and self.sheet:
            self.sheet.set_sheet_data(data=[])
            self.sheet.refresh()
    
    def add_row(self, row_data: List):
        """Add a new row to the table"""
        self.data.append(row_data)
        self.update_data(data=self.data)
    
    def remove_selected_row(self):
        """Remove currently selected row"""
        if TKSHEET_AVAILABLE and self.sheet:
            try:
                selected = self.sheet.get_currently_selected()
                if selected and selected.row is not None:
                    row_idx = selected.row
                    if 0 <= row_idx < len(self.data):
                        removed_row = self.data.pop(row_idx)
                        self.update_data(data=self.data)
                        return removed_row
            except Exception as e:
                print(f"Remove row error: {e}")
        return None
    
    def search_and_highlight(self, search_term: str):
        """Search for term in table and highlight results"""
        # This would require more advanced tksheet features
        # For now, just print search results
        if not search_term:
            return
        
        matching_rows = []
        for i, row in enumerate(self.data):
            for cell in row:
                if search_term.lower() in str(cell).lower():
                    matching_rows.append(i)
                    break
        
        print(f"🔍 Found {len(matching_rows)} matching rows for '{search_term}'")
        return matching_rows

class AsyncDataTable(DataTable):
    """
    Async version of DataTable for loading data from database
    """
    
    def __init__(self, master, data_loader: Callable = None, **kwargs):
        self.data_loader = data_loader
        self.loading = False
        super().__init__(master, **kwargs)
        
        if data_loader:
            self.load_data_async()
    
    def load_data_async(self):
        """Load data asynchronously"""
        if self.loading or not self.data_loader:
            return
        
        self.loading = True
        
        # Show loading indicator
        self.clear_data()
        if TKSHEET_AVAILABLE and self.sheet:
            self.sheet.set_sheet_data(data=[["Loading..."]])
            self.sheet.refresh()
        
        # Load data in background thread
        def load_data():
            try:
                headers, data = self.data_loader()
                # Update UI in main thread
                self.after(0, lambda: self._on_data_loaded(headers, data))
            except Exception as e:
                print(f"❌ Error loading data: {e}")
                self.after(0, lambda: self._on_data_error(str(e)))
        
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()
    
    def _on_data_loaded(self, headers: List[str], data: List[List]):
        """Handle successful data loading"""
        self.loading = False
        try:
            self.update_data(headers, data)
            print(f"✅ Loaded {len(data)} rows")
        except Exception as e:
            print(f"❌ Error updating table UI: {e}")
            self._on_data_error(f"UI Update Error: {str(e)}")
    
    def _on_data_error(self, error_msg: str):
        """Handle data loading error"""
        self.loading = False
        try:
            # Show user-friendly error message
            if "connection" in error_msg.lower():
                error_data = [["❌ Database connection failed", "Please check your database settings"]]
                headers = ["Error", "Message"]
            elif "mysql" in error_msg.lower():
                error_data = [["❌ Database error", "Please ensure MySQL is running"]]
                headers = ["Error", "Message"]
            else:
                error_data = [["❌ Error loading data", error_msg]]
                headers = ["Error", "Details"]
            
            self.update_data(headers, error_data)
        except Exception as e:
            print(f"❌ Error showing error message: {e}")
    
    def refresh_data(self):
        """Refresh table data"""
        if not self.loading:
            self.load_data_async()
