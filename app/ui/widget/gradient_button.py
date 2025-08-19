import customtkinter as ctk
import tkinter as tk
from typing import Union, Tuple, Optional, Callable


class GradientButton(ctk.CTkFrame):
    """
    Custom gradient button widget para sa modern UI
    Creates a beautiful gradient effect with hover states
    """
    
    def __init__(
        self,
        master,
        text: str = "Button",
        command: Optional[Callable] = None,
        width: int = 160,
        height: int = 40,
        start_color: str = "#3b82f6",
        end_color: str = "#1d4ed8",
        text_color: str = "white",
        hover_start_color: Optional[str] = None,
        hover_end_color: Optional[str] = None,
        font: Optional[ctk.CTkFont] = None,
        corner_radius: int = 8,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, corner_radius=corner_radius, **kwargs)
        
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.start_color = start_color
        self.end_color = end_color
        self.text_color = text_color
        self.hover_start_color = hover_start_color or self._brighten_color(start_color)
        self.hover_end_color = hover_end_color or self._brighten_color(end_color)
        self.font = font or ctk.CTkFont(size=14)
        self.corner_radius = corner_radius
        
        self._is_hovered = False
        self._create_widgets()
        self._bind_events()
    
    def _create_widgets(self):
        """Create the button widgets"""
        # Main button frame
        self.button_frame = ctk.CTkFrame(
            self,
            width=self.width,
            height=self.height,
            corner_radius=self.corner_radius,
            fg_color=self.start_color
        )
        self.button_frame.pack(fill="both", expand=True)
        self.button_frame.pack_propagate(False)
        
        # Text label
        self.label = ctk.CTkLabel(
            self.button_frame,
            text=self.text,
            font=self.font,
            text_color=self.text_color
        )
        self.label.pack(fill="both", expand=True)
        
        # Update gradient
        self._update_gradient()
    
    def _bind_events(self):
        """Bind mouse events for hover effects"""
        widgets = [self, self.button_frame, self.label]
        
        for widget in widgets:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
    
    def _on_click(self, event):
        """Handle button click"""
        if self.command:
            self.command()
    
    def _on_enter(self, event):
        """Handle mouse enter (hover)"""
        self._is_hovered = True
        self._update_gradient()
        self.configure(cursor="hand2")
    
    def _on_leave(self, event):
        """Handle mouse leave"""
        self._is_hovered = False
        self._update_gradient()
        self.configure(cursor="")
    
    def _update_gradient(self):
        """Update the gradient colors based on hover state"""
        if self._is_hovered:
            color = self.hover_start_color
        else:
            color = self.start_color
        
        self.button_frame.configure(fg_color=color)
    
    def _brighten_color(self, color: str, factor: float = 0.2) -> str:
        """Brighten a hex color by the given factor"""
        try:
            # Remove '#' if present
            color = color.lstrip('#')
            
            # Convert to RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Brighten each component
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            # Fallback to original color if conversion fails
            return color
    
    def configure_text(self, text: str):
        """Update button text"""
        self.text = text
        self.label.configure(text=text)
    
    def configure_command(self, command: Callable):
        """Update button command"""
        self.command = command
