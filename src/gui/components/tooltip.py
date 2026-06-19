import tkinter as tk
from typing import Optional

class Tooltip:
    """
    A lightweight, reliable, dark-themed hover tooltip for CustomTkinter widgets
    using a borderless Tkinter Toplevel window.
    """
    def __init__(self, widget, text: str, delay: int = 400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window: Optional[tk.Toplevel] = None
        self.id: Optional[str] = None
        
        # Bind hover/mouse events
        self.widget.bind("<Enter>", self.schedule, add="+")
        self.widget.bind("<Leave>", self.hide, add="+")
        self.widget.bind("<ButtonPress>", self.hide, add="+")
        
    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)
        
    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
            
    def show(self):
        self.unschedule()
        if self.tooltip_window:
            return
            
        # Determine root coordinate position directly below the target widget
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create borderless window container
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.configure(bg="#475569")  # Border grey
        
        # Inner text frame
        inner_frame = tk.Frame(self.tooltip_window, bg="#0f172a", bd=0)
        inner_frame.pack(padx=1, pady=1)
        
        # Label text widget
        lbl = tk.Label(
            inner_frame,
            text=self.text,
            justify="left",
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 9),
            padx=8,
            pady=4
        )
        lbl.pack()
        
        # Ensure it floats above other widgets
        self.tooltip_window.attributes("-topmost", True)
        
    def hide(self, event=None):
        self.unschedule()
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def create_tooltip(widget, text: str) -> Tooltip:
    """Helper utility to bind a tooltip helper to any CTk/Tk widget."""
    return Tooltip(widget, text)
