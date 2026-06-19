import webbrowser
import customtkinter as ctk
from typing import List, Set

from src.scraper.base import Product
from src.gui.styles import (
    FONT_FAMILY,
    BG_CARD,
    BG_ROW_ALT,
    BG_CARD_BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    ACCENT_BLUE_HOVER,
    STATUS_IN_STOCK,
    STATUS_OUT_OF_STOCK,
    STATUS_UNKNOWN
)
from src.gui.components.tooltip import create_tooltip

class ModernTable(ctk.CTkFrame):
    """
    A custom-built, modern, high-performance table widget with sorting,
    pagination, checkboxes for multi-row selection, action buttons, and tooltips.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.products: List[Product] = []
        self.filtered_products: List[Product] = []
        
        # Row Selection tracking
        self.selected_urls: Set[str] = set()
        
        # Pagination state
        self.current_page = 1
        self.items_per_page = 15
        
        # Sorting state
        # (column_key, reverse)
        self.sort_state = ("name", False) 
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Scrollable table area gets all extra space
        
        # --- HEADERS FRAME ---
        self.headers_frame = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            height=40,
            corner_radius=6,
            border_width=1,
            border_color=BG_CARD_BORDER
        )
        self.headers_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Columns layout
        # Col 0: Checkbox, Col 1: Index, Col 2: Name, Col 3: Price, Col 4: Rating, Col 5: Status, Col 6: Actions
        self.column_weights = [1, 1, 6, 2, 2, 2, 2]
        for i, weight in enumerate(self.column_weights):
            self.headers_frame.grid_columnconfigure(i, weight=weight)
            
        # Select All Checkbox in Header
        self.select_all_var = ctk.BooleanVar(value=False)
        self.select_all_cb = ctk.CTkCheckBox(
            self.headers_frame,
            text="",
            variable=self.select_all_var,
            width=18,
            height=18,
            checkbox_width=18,
            checkbox_height=18,
            command=self._on_select_all_clicked
        )
        self.select_all_cb.grid(row=0, column=0, padx=(12, 0), sticky="w")
        create_tooltip(self.select_all_cb, "Select or deselect all products in table")
        
        # Headers definitions (Col 1 to 6)
        self.headers_info = [
            ("#", None),
            ("Product Name", "name"),
            ("Price", "price_val"),
            ("Rating", "rating_val"),
            ("Availability", "availability"),
            ("Actions", None)
        ]
        
        self.header_buttons = []
        for i, (text, key) in enumerate(self.headers_info):
            col_idx = i + 1 # offset by 1 because of checkbox col
            if key:
                # Interactive header button for sorting
                btn = ctk.CTkButton(
                    self.headers_frame,
                    text=f"{text} ↕",
                    font=(FONT_FAMILY, 12, "bold"),
                    text_color=TEXT_PRIMARY,
                    fg_color="transparent",
                    hover_color="#334155",
                    anchor="w" if col_idx == 2 else "center",
                    command=lambda k=key: self._on_header_click(k)
                )
                btn.grid(row=0, column=col_idx, sticky="nsew", padx=3, pady=3)
                self.header_buttons.append((key, btn, text))
                create_tooltip(btn, f"Sort products by {text.lower()}")
            else:
                lbl = ctk.CTkLabel(
                    self.headers_frame,
                    text=text,
                    font=(FONT_FAMILY, 12, "bold"),
                    text_color=TEXT_SECONDARY,
                    anchor="center"
                )
                lbl.grid(row=0, column=col_idx, sticky="nsew", padx=3, pady=3)
                
        # --- SCROLLABLE DATA ROWS ---
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # --- PAGINATION CONTROLS ---
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.controls_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        
        self.prev_btn = ctk.CTkButton(
            self.controls_frame,
            text="◀ Previous",
            width=100,
            fg_color=BG_CARD,
            hover_color="#334155",
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BG_CARD_BORDER,
            command=self.prev_page
        )
        self.prev_btn.pack(side="left", padx=5)
        create_tooltip(self.prev_btn, "Show the previous page of products")
        
        self.page_lbl = ctk.CTkLabel(
            self.controls_frame,
            text="Page 1 of 1",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_SECONDARY
        )
        self.page_lbl.pack(side="left", fill="x", expand=True)
        
        self.next_btn = ctk.CTkButton(
            self.controls_frame,
            text="Next ▶",
            width=100,
            fg_color=BG_CARD,
            hover_color="#334155",
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BG_CARD_BORDER,
            command=self.next_page
        )
        self.next_btn.pack(side="right", padx=5)
        create_tooltip(self.next_btn, "Show the next page of products")
        
    def set_data(self, products: List[Product]):
        """Set new dataset, reset checkboxes, and reset pagination."""
        self.products = products
        self.filtered_products = products.copy()
        self.selected_urls.clear()
        self.select_all_var.set(value=False)
        self.current_page = 1
        self._apply_sort()
        
    def get_selected_products(self) -> List[Product]:
        """Return the list of Product objects currently selected by the checkboxes."""
        return [p for p in self.products if p.url in self.selected_urls]
        
    def update_display(self):
        """Redraw the table rows for the current page."""
        # Clear existing rows in scrollable frame
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.filtered_products[start_idx:end_idx]
        
        # Update pagination buttons state
        total_pages = max(1, (len(self.filtered_products) + self.items_per_page - 1) // self.items_per_page)
        self.page_lbl.configure(text=f"Page {self.current_page} of {total_pages} (Showing {start_idx + 1}-{min(end_idx, len(self.filtered_products))} of {len(self.filtered_products)})")
        
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        
        if not page_items:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="No products to display.",
                font=(FONT_FAMILY, 14, "italic"),
                text_color=TEXT_MUTED
            )
            empty_lbl.pack(pady=40)
            return
            
        # Draw rows
        for idx, prod in enumerate(page_items):
            row_num = start_idx + idx + 1
            bg_color = BG_ROW_ALT if idx % 2 == 0 else "transparent"
            
            row_frame = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=bg_color,
                corner_radius=4,
                height=36
            )
            row_frame.pack(fill="x", pady=1)
            
            for col_idx, weight in enumerate(self.column_weights):
                row_frame.grid_columnconfigure(col_idx, weight=weight)
                
            # Column 0: Selection Checkbox
            is_selected = prod.url in self.selected_urls
            cb_var = ctk.BooleanVar(value=is_selected)
            cb = ctk.CTkCheckBox(
                row_frame,
                text="",
                variable=cb_var,
                width=18,
                height=18,
                checkbox_width=18,
                checkbox_height=18,
                command=lambda p=prod, v=cb_var: self._on_row_select_clicked(p, v)
            )
            cb.grid(row=0, column=0, padx=(12, 0), sticky="w")
            
            # Column 1: Index
            lbl_idx = ctk.CTkLabel(row_frame, text=str(row_num), font=(FONT_FAMILY, 11), text_color=TEXT_MUTED)
            lbl_idx.grid(row=0, column=1, sticky="nsew", padx=5)
            
            # Column 2: Name (truncated if too long, with anchor West)
            name_text = prod.name
            if len(name_text) > 55:
                name_text = name_text[:52] + "..."
            lbl_name = ctk.CTkLabel(row_frame, text=name_text, font=(FONT_FAMILY, 12), text_color=TEXT_PRIMARY, anchor="w")
            lbl_name.grid(row=0, column=2, sticky="nsew", padx=5)
            
            # Attach full name tooltip to title
            if len(prod.name) > 55:
                create_tooltip(lbl_name, prod.name)
            
            # Column 3: Price
            lbl_price = ctk.CTkLabel(row_frame, text=prod.price_str, font=(FONT_FAMILY, 12, "bold"), text_color=TEXT_PRIMARY)
            lbl_price.grid(row=0, column=3, sticky="nsew", padx=5)
            
            # Column 4: Rating
            lbl_rating = ctk.CTkLabel(row_frame, text=prod.rating_str, font=(FONT_FAMILY, 11), text_color=ACCENT_BLUE)
            lbl_rating.grid(row=0, column=4, sticky="nsew", padx=5)
            
            # Column 5: Availability (Badge)
            status = prod.availability.lower()
            status_color = STATUS_UNKNOWN
            if "in stock" in status or "instock" in status or "available" in status:
                status_color = STATUS_IN_STOCK
            elif "out of stock" in status or "unavailable" in status:
                status_color = STATUS_OUT_OF_STOCK
                
            lbl_status = ctk.CTkLabel(
                row_frame,
                text=prod.availability,
                font=(FONT_FAMILY, 11, "bold"),
                text_color=status_color
            )
            lbl_status.grid(row=0, column=5, sticky="nsew", padx=5)
            
            # Column 6: Action Button
            btn_action = ctk.CTkButton(
                row_frame,
                text="View Product",
                font=(FONT_FAMILY, 10, "bold"),
                fg_color=BG_CARD,
                hover_color=ACCENT_BLUE_HOVER,
                border_width=1,
                border_color=BG_CARD_BORDER,
                text_color=TEXT_PRIMARY,
                height=24,
                width=80,
                corner_radius=4,
                command=lambda url=prod.url: webbrowser.open(url)
            )
            btn_action.grid(row=0, column=6, sticky="center", padx=5, pady=4)
            
            create_tooltip(btn_action, f"Open product link in browser:\n{prod.url}")
            
    def _on_select_all_clicked(self):
        """Toggle checkboxes of all filtered items."""
        checked = self.select_all_var.get()
        if checked:
            for p in self.filtered_products:
                self.selected_urls.add(p.url)
        else:
            self.selected_urls.clear()
        self.update_display()
        
    def _on_row_select_clicked(self, product: Product, variable: ctk.BooleanVar):
        """Toggle checkbox selection for a single row."""
        checked = variable.get()
        if checked:
            self.selected_urls.add(product.url)
        else:
            self.selected_urls.discard(product.url)
            # If any is deselected, header Select All checkbox should clear
            self.select_all_var.set(value=False)
            
    def _on_header_click(self, key: str):
        """Handle column header click for sorting."""
        current_col, reverse = self.sort_state
        if current_col == key:
            reverse = not reverse
        else:
            reverse = False
            
        self.sort_state = (key, reverse)
        self._apply_sort()
        
    def _apply_sort(self):
        """Sort the filtered products array based on sort_state."""
        key, reverse = self.sort_state
        
        # Update header arrows
        for col_key, btn, text in self.header_buttons:
            if col_key == key:
                arrow = " ▼" if reverse else " ▲"
                btn.configure(text=f"{text}{arrow}", text_color=ACCENT_BLUE)
            else:
                btn.configure(text=f"{text} ↕", text_color=TEXT_PRIMARY)
                
        # Sort function
        if key == "name":
            self.filtered_products.sort(key=lambda x: x.name.lower(), reverse=reverse)
        elif key == "price_val":
            self.filtered_products.sort(key=lambda x: x.price_val, reverse=reverse)
        elif key == "rating_val":
            self.filtered_products.sort(key=lambda x: x.rating_val, reverse=reverse)
        elif key == "availability":
            self.filtered_products.sort(key=lambda x: x.availability.lower(), reverse=reverse)
            
        self.current_page = 1
        self.update_display()
        
    def apply_filters(self, search_query: str, min_price: float, max_price: float, min_rating: float):
        """Apply filters to the dataset."""
        q = search_query.strip().lower()
        
        filtered = []
        for p in self.products:
            # Search filter
            if q and q not in p.name.lower() and q not in p.availability.lower():
                continue
                
            # Price filter
            if p.price_val < min_price or (max_price > 0 and p.price_val > max_price):
                continue
                
            # Rating filter
            if p.rating_val < min_rating:
                continue
                
            filtered.append(p)
            
        self.filtered_products = filtered
        self.current_page = 1
        self._apply_sort()
        
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_display()
            
    def next_page(self):
        total_pages = max(1, (len(self.filtered_products) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_display()
