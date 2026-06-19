import customtkinter as ctk
from typing import Dict

from src.gui.styles import (
    FONT_FAMILY,
    BG_CARD,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
)

class RulesPanel(ctk.CTkFrame):
    """
    Panel for configuring scraping engines and advanced Custom CSS selectors.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Header title
        title_lbl = ctk.CTkLabel(
            self,
            text="Scraping Rules & Selectors",
            font=(FONT_FAMILY, 20, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(fill="x", pady=(10, 5))
        
        subtitle_lbl = ctk.CTkLabel(
            self,
            text="Configure how the scraping engine should locate and extract data fields.",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_SECONDARY,
            anchor="w"
        )
        subtitle_lbl.pack(fill="x", pady=(0, 20))
        
        # --- SELECT ENGINE BOX ---
        engine_box = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8)
        engine_box.pack(fill="x", pady=(0, 15))
        
        engine_title = ctk.CTkLabel(
            engine_box,
            text="1. Choose Scraping Engine",
            font=(FONT_FAMILY, 14, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )
        engine_title.pack(fill="x", pady=(5, 10), padx=16)
        
        self.engine_var = ctk.StringVar(value="autodetect")
        
        # Radio buttons
        r1 = ctk.CTkRadioButton(
            engine_box,
            text="Smart Auto-Detect (JSON-LD & OpenGraph)",
            value="autodetect",
            variable=self.engine_var,
            font=(FONT_FAMILY, 12),
            command=self._on_engine_change
        )
        r1.pack(fill="x", padx=16, pady=5)
        
        r2 = ctk.CTkRadioButton(
            engine_box,
            text="Books to Scrape Sandbox (Pre-configured Demo)",
            value="books_to_scrape",
            variable=self.engine_var,
            font=(FONT_FAMILY, 12),
            command=self._on_engine_change
        )
        r2.pack(fill="x", padx=16, pady=5)
        
        r3 = ctk.CTkRadioButton(
            engine_box,
            text="Custom CSS Selectors (For advanced scraping)",
            value="custom_css",
            variable=self.engine_var,
            font=(FONT_FAMILY, 12),
            command=self._on_engine_change
        )
        r3.pack(fill="x", padx=16, pady=5)
        
        # --- CUSTOM SELECTORS FORM ---
        self.custom_form = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8)
        self.custom_form.pack(fill="both", expand=True, pady=(0, 10))
        
        form_title = ctk.CTkLabel(
            self.custom_form,
            text="2. Configure Custom CSS Selectors",
            font=(FONT_FAMILY, 14, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )
        form_title.pack(fill="x", padx=16, pady=(16, 5))
        
        desc_lbl = ctk.CTkLabel(
            self.custom_form,
            text="Standard BeautifulSoup .select() rules. Leave fields blank to let engine try defaults.",
            font=(FONT_FAMILY, 11),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        desc_lbl.pack(fill="x", padx=16, pady=(0, 15))
        
        # Fields configuration
        self.selector_inputs = {}
        fields = [
            ("container", "Product Card/Box Selector", ".product_pod", "Matches the outer element container of a single product"),
            ("name", "Product Name Selector", "h3 > a", "Matches title element relative to container"),
            ("price", "Price Selector", ".price_color", "Matches price element relative to container"),
            ("rating", "Rating Selector", ".star-rating", "Matches rating classes/text relative to container"),
            ("availability", "Availability Status Selector", ".instock.availability", "Matches stock/avail status text relative to container"),
            ("url", "Product Link/URL Selector", "h3 > a", "Matches the link href target relative to container"),
            ("next_page", "Next Page Button Selector", "li.next > a", "Matches the pagination next link button (global page relative)")
        ]
        
        # Grid frame inside form
        grid_frame = ctk.CTkFrame(self.custom_form, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=16, pady=5)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=2)
        
        for idx, (key, label, placeholder, help_text) in enumerate(fields):
            lbl_field = ctk.CTkLabel(
                grid_frame,
                text=label,
                font=(FONT_FAMILY, 12, "bold"),
                text_color=TEXT_PRIMARY,
                anchor="w"
            )
            lbl_field.grid(row=idx, column=0, sticky="w", pady=6, padx=(0, 10))
            
            entry = ctk.CTkEntry(
                grid_frame,
                placeholder_text=placeholder,
                font=(FONT_FAMILY, 12),
                height=28
            )
            entry.grid(row=idx, column=1, sticky="ew", pady=6)
            
            self.selector_inputs[key] = entry
            
        # Hide custom form initially (since auto-detect is default)
        self._on_engine_change()
        
    def _on_engine_change(self):
        engine = self.engine_var.get()
        if engine == "custom_css":
            # Enable custom form input controls
            for entry in self.selector_inputs.values():
                entry.configure(state="normal", fg_color="#1a1a20")
        else:
            # Disable custom form input controls to avoid confusion
            for entry in self.selector_inputs.values():
                entry.configure(state="disabled", fg_color="#282830")
                
    def get_selectors(self) -> Dict[str, str]:
        """Get the user-defined CSS selectors."""
        return {
            key: entry.get().strip()
            for key, entry in self.selector_inputs.items()
        }
        
    def get_engine_type(self) -> str:
        """Get active scraping engine choice."""
        return self.engine_var.get()
        
    def set_engine_type(self, engine: str):
        """Set active scraping engine choice programmatically."""
        self.engine_var.set(engine)
        self._on_engine_change()
