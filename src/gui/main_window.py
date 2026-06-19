import time
import queue
import logging
import threading
import base64
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional

from src.scraper import ScraperFactory, ScraperConfig, Product
from src.utils.exporter import export_to_csv, export_to_excel
from src.utils.helpers import is_valid_url
from src.utils.history import save_session, get_all_sessions, delete_session, clear_all_history
from src.utils.validation import validate_and_sanitize_products
from src.gui.styles import (
    FONT_FAMILY,
    BG_MAIN,
    BG_SIDEBAR,
    BG_CARD,
    BG_CARD_BORDER,
    BG_INPUT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    ACCENT_BLUE_HOVER,
    ACCENT_GREEN,
    ACCENT_GREEN_HOVER,
    ACCENT_RED,
    ACCENT_RED_HOVER,
    ACCENT_AMBER
)
from src.gui.components.table import ModernTable
from src.gui.components.rules_panel import RulesPanel
from src.gui.components.tooltip import create_tooltip

logger = logging.getLogger(__name__)

ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6"
    "JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAACXBIWXMAAAsTAAALEwEAmpwYAAAEcElE"
    "QVR4Ae2Vz2sTQRTHv2mz2Wxqm7T50VptK61i/VEtVqogqAdP9iB48CAIevDkoYceevbkpQdBDx7Eg8f+"
    "AYVCoVAo2kK1prap+dO0SZvsbnZn3qwmsX/A6sK+8IaZt+P7zHvz3rwdfpumadI/lhK56UisP8wDk8U8"
    "oA+gH9APMIHkP8X5z5K5L2B+wP6A/wETWNzC5rM9s8d3+f/E5sVn1L1+U77fNfM3bWwsW8D2pM1tD5vX"
    "D2tD38N90CewF1pXm4FpYV0031vH+79P3XF4cZ4LwZc/uD+f5sK2hW2D68L3tDVsLdsQ1tH72EezTfRj"
    "WIdH6EewDo/4D1yH+qP6o/qD/rA+Bv4/gHqTjV+oN9l4iHqTjV+ot6uNZRtoG9gP9kM9g/pZ1M+ifhb1"
    "M6ifRf1sT1vD1thHsA/qS+hHsA735z6hH6N+mI330G8T/TbpT9FvE/1O9O/H5uFmQnOznGzmOdnM/WlO"
    "NnPLznKymbVf42Qz62M2sz6mP2Qzm5/yKJs/vX4vR5vX6+J1Zc7g4tZ4tY/X1fO6el4Xr/dxf+D2H60N"
    "rP8G1o3H9sBtsLUPbkf2wG0fXoPbg/uxPXjExiP7oF4U60WhXhTqxbBeDOvFsF7MPrw2t6G+gH4R/SL6"
    "RfSL6BfRL6Jf9Inbf0x/TH9Mf0R/yH4I2wdtDVsH9nC12cW+w+vC1w+z7/G68D1sHbaOrYXW0dawNZrv"
    "rdv4hXrjF+qNR2y8j34P/R76UfazqJ9E/STqZ1E/i/pZ1E+y9mvZzNqvZTPrY9nHZDObt2Yz10fW5z+Y"
    "n8Pmsz2bx+vC1x+3x3fZ/rD52xY2ny1se9K2h+3B13C12ce+J/tPUPf6w81wP3X/L2xefEb95Zvy74vN"
    "iwuB/+J7eNqGbcM2sA1sA9vANmwD28C2wW1gG9iGbcP3sG34Hq42+3D/AezD/YHbD2Af7g/6g/6wPujP"
    "a1M4r01h/XltiutfzGtT1n83WdYvZFm/gH4B/QL62Z79Z86m1v9ztrT+n7KldT5l/b9jS1szW1rnU9b5"
    "lHX+x36K5fW57KccW8pxv19uKceWctz3yy3l2DKO+wPl2DK+F1qOfbgf5djYctyPcnwsOb7X7x2W4/s4"
    "t/d/k1t+fK//HZaP8f1m2W/2uXy+2exl9jJ7mb3MXjbf7GX2MnuZvWzf7GX2Mvu/zN5m7z6v3WfP9mz3"
    "7M92z/5s9+zPds/+bPfsz3bP9u42t3fb9GZ4vW5q0+ulNr1ealPmtS5e6+K1ZfG6Mte6eF2eW78t2/6u"
    "67au26r/L3K1V/f6T5Z+q9X7v+eW3v89t/T+77mldz5mndexpef5tL3/eWzpWZ/P9vlcn8/1ebx+j9fD"
    "e/72/Q2b4T17xHvw+GvGe6D9N+0Rsj/bL7PH+wM2Hz272j7s/yZbWP5xNrf842xu/yebP8H+j7P/E5uP"
    "nmkL2x5vIeP5w9vI+GvGW8A+bAPbwDawDWwD27ANbMPrwP/ANmwDvpe2Pdy/3/9TtrSef8qW1vkf+z8A"
    "gWpA34V7RbgAAAAASUVORK5CYII="
)

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Product Scraper Pro")
        self.geometry("1150x760")
        self.minsize(1050, 700)
        self._load_app_icon()
        
        self.scraped_products: List[Product] = []
        self.scraping_thread: Optional[threading.Thread] = None
        self.active_scraper = None
        self.scraping_queue = queue.Queue()
        self.scrape_start_time = 0.0
        self.spinner_idx = 0
        
        # Scraper Settings Variables
        self.max_pages_var = ctk.IntVar(value=3)
        self.timeout_var = ctk.IntVar(value=10)
        self.delay_var = ctk.DoubleVar(value=0.5)
        
        # Advanced Data Settings Variables
        self.deduplicate_var = ctk.BooleanVar(value=True)
        self.autosave_var = ctk.BooleanVar(value=True)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self._setup_ui()
        self.change_view("dashboard")
        
    def _load_app_icon(self):
        try:
            icon_data = base64.b64decode(ICON_BASE64)
            app_icon = tk.PhotoImage(data=icon_data)
            self.iconphoto(True, app_icon)
        except Exception as e:
            logger.warning(f"Could not load application icon: {e}")
            
    def _setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        # --- SIDEBAR NAVIGATION ---
        self.sidebar = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, width=230, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        logo_lbl = ctk.CTkLabel(self.sidebar, text="PRO SCRAPER", font=(FONT_FAMILY, 22, "bold"), text_color=ACCENT_BLUE)
        logo_lbl.pack(pady=(35, 3))
        version_lbl = ctk.CTkLabel(self.sidebar, text="Advanced Catalog Extractor", font=(FONT_FAMILY, 11), text_color=TEXT_MUTED)
        version_lbl.pack(pady=(0, 30))
        
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("dashboard", "Dashboard", "📊", "Access scraping controls, stats, and filtered products table"),
            ("history", "Scraping History", "📜", "Review and reload previous scraping sessions"),
            ("rules", "Scraping Rules", "⚙️", "Configure targets and customize CSS selectors"),
            ("settings", "Settings", "🔧", "Modify request limits, timeouts, and polite scraping delays"),
            ("about", "About", "ℹ️", "View framework libraries and engine properties")
        ]
        
        for view_name, label, icon, tooltip_text in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {label}",
                font=(FONT_FAMILY, 13, "bold"),
                anchor="w",
                fg_color="transparent",
                hover_color="#334155",
                text_color=TEXT_PRIMARY,
                height=42,
                corner_radius=6,
                command=lambda v=view_name: self.change_view(v)
            )
            btn.pack(fill="x", padx=15, pady=4)
            self.nav_buttons[view_name] = btn
            create_tooltip(btn, tooltip_text)
            
        self.sidebar_bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_bottom.pack(side="bottom", fill="x", padx=15, pady=25)
        
        theme_lbl = ctk.CTkLabel(self.sidebar_bottom, text="Theme Mode:", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_SECONDARY)
        theme_lbl.pack(fill="x", anchor="w", pady=(0, 4))
        
        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar_bottom,
            values=["Dark", "Light", "System"],
            font=(FONT_FAMILY, 11),
            height=26,
            fg_color=BG_MAIN,
            button_color=BG_MAIN,
            button_hover_color="#334155",
            dropdown_fg_color=BG_MAIN,
            dropdown_hover_color="#334155",
            command=self._on_theme_change
        )
        self.theme_menu.pack(fill="x")
        create_tooltip(self.theme_menu, "Toggle interface color scheme theme mode")
        
        # --- MAIN CONTAINER ---
        self.main_container = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # --- BOTTOM STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, height=28, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_dot = ctk.CTkFrame(self.status_bar, width=12, height=12, corner_radius=6, fg_color=ACCENT_GREEN)
        self.status_dot.pack(side="left", padx=(12, 2), pady=8)
        
        self.status_bar_lbl = ctk.CTkLabel(self.status_bar, text="System ready", font=(FONT_FAMILY, 11), text_color=TEXT_SECONDARY)
        self.status_bar_lbl.pack(side="left")
        
        self.status_bar_right = ctk.CTkLabel(self.status_bar, text="Engine: Auto-Detect | Scraper Pro v1.0.0", font=(FONT_FAMILY, 11), text_color=TEXT_MUTED)
        self.status_bar_right.pack(side="right", padx=15)
        
        # Initialize sub-views
        self.views: Dict[str, ctk.CTkFrame] = {
            "dashboard": self._create_dashboard_view(),
            "history": self._create_history_view(),
            "rules": self._create_rules_view(),
            "settings": self._create_settings_view(),
            "about": self._create_about_view()
        }
        
    def change_view(self, target_view: str):
        for name, frame in self.views.items():
            if name == target_view:
                frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=(20, 15))
                self.nav_buttons[name].configure(fg_color="#334155", text_color=ACCENT_BLUE)
                # If switching to history view, refresh historical list
                if name == "history":
                    self._refresh_history_view()
            else:
                frame.grid_forget()
                self.nav_buttons[name].configure(fg_color="transparent", text_color=TEXT_PRIMARY)
                
    # ==========================================
    # VIEW CREATORS
    # ==========================================
    
    def _create_dashboard_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(4, weight=1)
        
        # 1. URL input card
        input_card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BG_CARD_BORDER)
        input_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        input_card.grid_columnconfigure(1, weight=1)
        
        url_lbl = ctk.CTkLabel(input_card, text="Target URL:", font=(FONT_FAMILY, 12, "bold"), text_color=TEXT_PRIMARY)
        url_lbl.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="w")
        
        self.url_entry = ctk.CTkEntry(
            input_card, placeholder_text="http://books.toscrape.com/", font=(FONT_FAMILY, 12),
            fg_color=BG_INPUT, border_color=BG_CARD_BORDER, height=32
        )
        self.url_entry.grid(row=0, column=1, padx=5, pady=12, sticky="ew")
        self.url_entry.insert(0, "http://books.toscrape.com/")
        create_tooltip(self.url_entry, "Enter the e-commerce website address link to scrape")
        
        self.scrape_btn = ctk.CTkButton(
            input_card, text="Start Scraping", font=(FONT_FAMILY, 12, "bold"),
            fg_color=ACCENT_GREEN, hover_color=ACCENT_GREEN_HOVER, text_color="#0f172a",
            height=32, width=120, command=self.start_scraping
        )
        self.scrape_btn.grid(row=0, column=2, padx=5, pady=12)
        create_tooltip(self.scrape_btn, "Fetch website content and extract items in a safe background thread")
        
        self.cancel_btn = ctk.CTkButton(
            input_card, text="Cancel", font=(FONT_FAMILY, 12, "bold"),
            fg_color=ACCENT_RED, hover_color=ACCENT_RED_HOVER, text_color=TEXT_PRIMARY,
            height=32, width=80, state="disabled", command=self.cancel_scraping
        )
        self.cancel_btn.grid(row=0, column=3, padx=5, pady=12)
        create_tooltip(self.cancel_btn, "Stop the active scraping thread at the next page boundary")
        
        self.clear_btn = ctk.CTkButton(
            input_card, text="Clear", font=(FONT_FAMILY, 12, "bold"),
            fg_color=BG_MAIN, hover_color="#334155", border_width=1, border_color=BG_CARD_BORDER,
            text_color=TEXT_PRIMARY, height=32, width=80, state="disabled", command=self.clear_results
        )
        self.clear_btn.grid(row=0, column=4, padx=(5, 16), pady=12)
        create_tooltip(self.clear_btn, "Clear currently scraped dataset results from the dashboard")
        
        # 2. Progress bar
        self.progress_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=6, progress_color=ACCENT_BLUE, fg_color=BG_CARD_BORDER)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.progress_bar.set(0)
        
        # 3. Stats cards
        stats_container = ctk.CTkFrame(frame, fg_color="transparent")
        stats_container.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        for col_idx in range(4):
            stats_container.grid_columnconfigure(col_idx, weight=1)
            
        stats_definitions = [
            ("scraped", "📦 PRODUCTS SCRAPED", "0", ACCENT_BLUE, "Total count of products matching current filters"),
            ("avg", "📊 AVERAGE PRICE", "N/A", ACCENT_AMBER, "Average price of the currently shown product subset"),
            ("high", "📈 HIGHEST PRICE", "N/A", ACCENT_GREEN, "Maximum price among currently filtered items"),
            ("low", "📉 LOWEST PRICE", "N/A", ACCENT_RED, "Minimum price among currently filtered items")
        ]
        
        self.stats_cards = {}
        for idx, (key, label, val_default, color, tooltip_msg) in enumerate(stats_definitions):
            card = ctk.CTkFrame(stats_container, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BG_CARD_BORDER)
            card.grid(row=0, column=idx, padx=4 if 0 < idx < 3 else (0 if idx==0 else 4, 0 if idx==3 else 4), sticky="nsew")
            
            lbl_title = ctk.CTkLabel(card, text=label, font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_SECONDARY)
            lbl_title.pack(anchor="w", padx=12, pady=(10, 2))
            
            lbl_val = ctk.CTkLabel(card, text=val_default, font=(FONT_FAMILY, 20, "bold"), text_color=color)
            lbl_val.pack(anchor="w", padx=12, pady=(0, 10))
            
            self.stats_cards[key] = lbl_val
            create_tooltip(card, tooltip_msg)
            
        # 4. Filters card panel
        filters_card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BG_CARD_BORDER)
        filters_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        filters_card.grid_columnconfigure(0, weight=3)
        filters_card.grid_columnconfigure(1, weight=1)
        filters_card.grid_columnconfigure(2, weight=1)
        
        search_frame = ctk.CTkFrame(filters_card, fg_color="transparent")
        search_frame.grid(row=0, column=0, padx=12, pady=10, sticky="nsew")
        ctk.CTkLabel(search_frame, text="Search Keywords:", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_SECONDARY, anchor="w").pack(fill="x")
        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Filter items by product name...", font=(FONT_FAMILY, 12),
            fg_color=BG_INPUT, border_color=BG_CARD_BORDER, height=26
        )
        self.search_entry.pack(fill="x", pady=(3, 0))
        self.search_entry.bind("<KeyRelease>", self._on_filter_changed)
        create_tooltip(self.search_entry, "Filters products instantly as you type")
        
        rating_frame = ctk.CTkFrame(filters_card, fg_color="transparent")
        rating_frame.grid(row=0, column=1, padx=12, pady=10, sticky="nsew")
        ctk.CTkLabel(rating_frame, text="Min Star Rating:", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_SECONDARY, anchor="w").pack(fill="x")
        self.rating_filter_menu = ctk.CTkOptionMenu(
            rating_frame, values=["Any", "1+ Star", "2+ Stars", "3+ Stars", "4+ Stars", "5 Stars"],
            font=(FONT_FAMILY, 11), height=26, fg_color=BG_MAIN, button_color=BG_MAIN,
            button_hover_color="#334155", dropdown_fg_color=BG_MAIN, dropdown_hover_color="#334155",
            command=self._on_filter_changed
        )
        self.rating_filter_menu.pack(fill="x", pady=(3, 0))
        create_tooltip(self.rating_filter_menu, "Exclude products below this star rating threshold")
        
        price_frame = ctk.CTkFrame(filters_card, fg_color="transparent")
        price_frame.grid(row=0, column=2, padx=12, pady=10, sticky="nsew")
        ctk.CTkLabel(price_frame, text="Price Range Limit:", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_SECONDARY, anchor="w").pack(fill="x")
        price_inputs = ctk.CTkFrame(price_frame, fg_color="transparent")
        price_inputs.pack(fill="x", pady=(3, 0))
        
        self.price_min_entry = ctk.CTkEntry(
            price_inputs, placeholder_text="Min", font=(FONT_FAMILY, 11),
            fg_color=BG_INPUT, border_color=BG_CARD_BORDER, height=26, width=58
        )
        self.price_min_entry.pack(side="left")
        self.price_min_entry.bind("<KeyRelease>", self._on_filter_changed)
        create_tooltip(self.price_min_entry, "Minimum numeric unit price threshold")
        
        ctk.CTkLabel(price_inputs, text="-", text_color=TEXT_SECONDARY, font=(FONT_FAMILY, 12)).pack(side="left", padx=4)
        
        self.price_max_entry = ctk.CTkEntry(
            price_inputs, placeholder_text="Max", font=(FONT_FAMILY, 11),
            fg_color=BG_INPUT, border_color=BG_CARD_BORDER, height=26, width=58
        )
        self.price_max_entry.pack(side="left")
        self.price_max_entry.bind("<KeyRelease>", self._on_filter_changed)
        create_tooltip(self.price_max_entry, "Maximum numeric unit price threshold")
        
        # 5. Data table
        self.results_table = ModernTable(frame)
        self.results_table.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        
        # 6. Export footer
        export_footer = ctk.CTkFrame(frame, fg_color="transparent")
        export_footer.grid(row=5, column=0, sticky="ew")
        
        export_lbl = ctk.CTkLabel(export_footer, text="Save Selected Products:", font=(FONT_FAMILY, 12, "bold"), text_color=TEXT_SECONDARY)
        export_lbl.pack(side="left", padx=(5, 10))
        
        self.export_csv_btn = ctk.CTkButton(
            export_footer, text="📄 Export to CSV", font=(FONT_FAMILY, 12, "bold"),
            fg_color=BG_CARD, hover_color=ACCENT_BLUE_HOVER, border_width=1, border_color=BG_CARD_BORDER,
            text_color=TEXT_PRIMARY, width=135, state="disabled", command=self.export_csv
        )
        self.export_csv_btn.pack(side="left", padx=5)
        create_tooltip(self.export_csv_btn, "Save the currently filtered dataset list (or checked selections only) as a CSV text sheet")
        
        self.export_excel_btn = ctk.CTkButton(
            export_footer, text="📈 Export to Excel", font=(FONT_FAMILY, 12, "bold"),
            fg_color=BG_CARD, hover_color=ACCENT_BLUE_HOVER, border_width=1, border_color=BG_CARD_BORDER,
            text_color=TEXT_PRIMARY, width=135, state="disabled", command=self.export_excel
        )
        self.export_excel_btn.pack(side="left", padx=5)
        create_tooltip(self.export_excel_btn, "Save the currently filtered dataset list (or checked selections only) as an Excel sheet")
        
        return frame
        
    def _create_history_view(self) -> ctk.CTkFrame:
        """Create the Scraping History tab view."""
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1) # History list expands
        
        # Title
        title_lbl = ctk.CTkLabel(frame, text="Scraping Sessions History", font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_PRIMARY, anchor="w")
        title_lbl.grid(row=0, column=0, sticky="w", pady=(10, 2))
        
        subtitle_lbl = ctk.CTkLabel(frame, text="Reload previous sessions directly into the active dashboard table.", font=(FONT_FAMILY, 12), text_color=TEXT_SECONDARY, anchor="w")
        subtitle_lbl.grid(row=1, column=0, sticky="w", pady=(0, 15))
        
        # Sessions scroll list
        self.history_scroll = ctk.CTkScrollableFrame(
            frame, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BG_CARD_BORDER
        )
        self.history_scroll.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        self.history_scroll.grid_columnconfigure(0, weight=1)
        
        # Wipe all button
        history_footer = ctk.CTkFrame(frame, fg_color="transparent")
        history_footer.grid(row=3, column=0, sticky="ew")
        
        self.clear_history_btn = ctk.CTkButton(
            history_footer, text="🗑️ Clear All Sessions History", font=(FONT_FAMILY, 12, "bold"),
            fg_color=BG_CARD, hover_color=ACCENT_RED_HOVER, border_width=1, border_color=BG_CARD_BORDER,
            text_color=TEXT_PRIMARY, width=220, command=self.clear_all_history
        )
        self.clear_history_btn.pack(side="left")
        create_tooltip(self.clear_history_btn, "Wipe the JSON database file containing previous runs history")
        
        return frame
        
    def _create_rules_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.rules_panel = RulesPanel(frame)
        self.rules_panel.pack(fill="both", expand=True, padx=5, pady=5)
        return frame
        
    def _create_settings_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        title_lbl = ctk.CTkLabel(frame, text="Scraping Settings", font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_PRIMARY, anchor="w")
        title_lbl.pack(fill="x", pady=(10, 5))
        
        subtitle_lbl = ctk.CTkLabel(frame, text="Adjust limits, polite delays, and advanced data cleaning configurations.", font=(FONT_FAMILY, 12), text_color=TEXT_SECONDARY, anchor="w")
        subtitle_lbl.pack(fill="x", pady=(0, 20))
        
        body = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BG_CARD_BORDER)
        body.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Max Pages Settings
        max_pages_frame = ctk.CTkFrame(body, fg_color="transparent")
        max_pages_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(max_pages_frame, text="Maximum Pages to Scrape (0 = unlimited):", font=(FONT_FAMILY, 13, "bold"), text_color=TEXT_PRIMARY, width=240, anchor="w").pack(side="left")
        self.max_pages_entry = ctk.CTkEntry(max_pages_frame, textvariable=self.max_pages_var, width=80, font=(FONT_FAMILY, 12), fg_color=BG_INPUT, border_color=BG_CARD_BORDER)
        self.max_pages_entry.pack(side="left")
        create_tooltip(self.max_pages_entry, "Configures the crawl page limit for multi-page engines. Use 0 to scrape all available pages.")
        ctk.CTkLabel(max_pages_frame, text="Set 0 to scrape all pages, or limit to prevent server overload.", font=(FONT_FAMILY, 11), text_color=TEXT_MUTED).pack(side="left", padx=15)
        
        # Request Timeout Settings
        timeout_frame = ctk.CTkFrame(body, fg_color="transparent")
        timeout_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(timeout_frame, text="Request Timeout (Seconds):", font=(FONT_FAMILY, 13, "bold"), text_color=TEXT_PRIMARY, width=200, anchor="w").pack(side="left")
        self.timeout_entry = ctk.CTkEntry(timeout_frame, textvariable=self.timeout_var, width=80, font=(FONT_FAMILY, 12), fg_color=BG_INPUT, border_color=BG_CARD_BORDER)
        self.timeout_entry.pack(side="left")
        create_tooltip(self.timeout_entry, "Aborts requests if the site doesn't reply within this duration")
        ctk.CTkLabel(timeout_frame, text="Drop connection if target fails to respond.", font=(FONT_FAMILY, 11), text_color=TEXT_MUTED).pack(side="left", padx=15)
        
        # Delay rate limits
        delay_frame = ctk.CTkFrame(body, fg_color="transparent")
        delay_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(delay_frame, text="Polite Request Delay (Sec):", font=(FONT_FAMILY, 13, "bold"), text_color=TEXT_PRIMARY, width=200, anchor="w").pack(side="left")
        self.delay_entry = ctk.CTkEntry(delay_frame, textvariable=self.delay_var, width=80, font=(FONT_FAMILY, 12), fg_color=BG_INPUT, border_color=BG_CARD_BORDER)
        self.delay_entry.pack(side="left")
        create_tooltip(self.delay_entry, "Injects sleep intervals between pages to reduce server load")
        ctk.CTkLabel(delay_frame, text="Prevents target website IP rate-limit blocks.", font=(FONT_FAMILY, 11), text_color=TEXT_MUTED).pack(side="left", padx=15)
        
        # Advanced Data Settings Separator
        sep = ctk.CTkFrame(body, fg_color=BG_CARD_BORDER, height=1)
        sep.pack(fill="x", pady=15, padx=10)
        
        # Data Management checkboxes
        data_frame = ctk.CTkFrame(body, fg_color="transparent")
        data_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(data_frame, text="Data Management Options:", font=(FONT_FAMILY, 13, "bold"), text_color=TEXT_PRIMARY, width=200, anchor="w").pack(side="left")
        
        cb_dedup = ctk.CTkCheckBox(data_frame, text="Deduplicate products by URL", variable=self.deduplicate_var, font=(FONT_FAMILY, 12))
        cb_dedup.pack(side="left", padx=10)
        create_tooltip(cb_dedup, "Remove duplicate items automatically before updating results list")
        
        cb_save = ctk.CTkCheckBox(data_frame, text="Auto-save runs to local history", variable=self.autosave_var, font=(FONT_FAMILY, 12))
        cb_save.pack(side="left", padx=20)
        create_tooltip(cb_save, "Save scraped lists directly into local JSON file history")
        
        return frame
        
    def _create_about_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        title_lbl = ctk.CTkLabel(frame, text="About Product Scraper Pro", font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_PRIMARY, anchor="w")
        title_lbl.pack(fill="x", pady=(10, 5))
        
        body = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BG_CARD_BORDER)
        body.pack(fill="both", expand=True, padx=30, pady=30)
        
        logo = ctk.CTkLabel(body, text="🔍", font=("Segoe UI Symbol", 64), text_color=ACCENT_BLUE)
        logo.pack(pady=(10, 5))
        name = ctk.CTkLabel(body, text="Product Scraper Pro", font=(FONT_FAMILY, 18, "bold"), text_color=TEXT_PRIMARY)
        name.pack()
        desc = ctk.CTkLabel(body, text="A modular desktop catalog harvesting client designed with CustomTkinter.\nExtracts fields using structured microdata configurations and rotating User-Agents.", font=(FONT_FAMILY, 12), text_color=TEXT_SECONDARY, justify="center")
        desc.pack(pady=15)
        
        details_box = ctk.CTkFrame(body, fg_color=BG_MAIN, corner_radius=6, border_width=1, border_color=BG_CARD_BORDER)
        details_box.pack(fill="x", pady=10, padx=20)
        
        details_text = (
            "Environment parameters:\n"
            "• GUI Engine: CustomTkinter 5.2.2 (Theme: Slate Blue-Black)\n"
            "• Parser Core: Beautiful Soup 4 & Requests\n"
            "• Export Handlers: Pandas & OpenPyXL\n"
            "• Execution Scheme: Multi-threaded non-blocking queue"
        )
        details_lbl = ctk.CTkLabel(details_box, text=details_text, font=(FONT_FAMILY, 12), text_color=TEXT_SECONDARY, justify="left", anchor="w")
        details_lbl.pack(fill="x", padx=15, pady=15)
        
        copyright_lbl = ctk.CTkLabel(body, text="© 2026 DeepMind Antigravity. Licensed under MIT License.", font=(FONT_FAMILY, 11), text_color=TEXT_MUTED)
        copyright_lbl.pack(side="bottom", pady=10)
        
        return frame
        
    # ==========================================
    # CORE LOGIC & ACTIONS
    # ==========================================
    
    def _on_theme_change(self, choice: str) -> None:
        """Switch application theme mode."""
        ctk.set_appearance_mode(choice.lower())
        self.status_bar_lbl.configure(text=f"Theme switched to {choice} mode.")
        self.status_bar_right.configure(text=self.status_bar_right.cget("text"))
        
    def _map_rating_choice_to_min(self, rating_choice: str) -> float:
        """Convert the rating dropdown selection into a numeric threshold."""
        if "1+" in rating_choice:
            return 1.0
        if "2+" in rating_choice:
            return 2.0
        if "3+" in rating_choice:
            return 3.0
        if "4+" in rating_choice:
            return 4.0
        if "5" in rating_choice:
            return 5.0
        return 0.0

    def _on_filter_changed(self, event=None) -> None:
        """Handle changes in the search, rating, and price filters."""
        query = self.search_entry.get().strip()
        rating_choice = self.rating_filter_menu.get()
        min_rating = self._map_rating_choice_to_min(rating_choice)

        try:
            min_price = float(self.price_min_entry.get().strip()) if self.price_min_entry.get().strip() else 0.0
        except ValueError:
            min_price = 0.0

        try:
            max_price = float(self.price_max_entry.get().strip()) if self.price_max_entry.get().strip() else 0.0
        except ValueError:
            max_price = 0.0

        if max_price and min_price and max_price < min_price:
            max_price = min_price

        self.results_table.apply_filters(
            search_query=query,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating
        )
        self._update_stats_cards()

    def _update_stats_cards(self) -> None:
        filtered = self.results_table.filtered_products
        count = len(filtered)
        
        if count == 0:
            self.stats_cards["scraped"].configure(text="0")
            self.stats_cards["avg"].configure(text="N/A")
            self.stats_cards["high"].configure(text="N/A")
            self.stats_cards["low"].configure(text="N/A")
            return
            
        currency = ""
        for p in filtered:
            if p.price_str:
                for symbol in ["$", "£", "€", "¥", "zł", "kr", "Rs"]:
                    if symbol in p.price_str:
                        currency = symbol
                        break
                if currency:
                    break
                    
        prices = [p.price_val for p in filtered if p.price_val > 0.0]
        
        if prices:
            avg_val = sum(prices) / len(prices)
            high_val = max(prices)
            low_val = min(prices)
            
            self.stats_cards["avg"].configure(text=f"{currency}{avg_val:.2f}")
            self.stats_cards["high"].configure(text=f"{currency}{high_val:.2f}")
            self.stats_cards["low"].configure(text=f"{currency}{low_val:.2f}")
        else:
            self.stats_cards["avg"].configure(text="N/A")
            self.stats_cards["high"].configure(text="N/A")
            self.stats_cards["low"].configure(text="N/A")
            
        self.stats_cards["scraped"].configure(text=str(count))
        
    def start_scraping(self):
        target_url = self.url_entry.get().strip()
        if not target_url:
            messagebox.showerror("Error", "Please enter a website URL to scrape.")
            return

        if not is_valid_url(target_url):
            messagebox.showerror("Error", "Invalid URL. Ensure it starts with http:// or https://")
            return

        try:
            max_pages = int(self.max_pages_var.get())
            timeout = int(self.timeout_var.get())
            delay = float(self.delay_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Error", "Settings values must be valid numbers.")
            return

        if max_pages < 0:
            messagebox.showerror("Error", "Please set the maximum page count to 0 (unlimited) or a positive integer.")
            return

        if timeout < 1:
            messagebox.showerror("Error", "Timeout must be 1 second or greater.")
            return

        if delay < 0:
            messagebox.showerror("Error", "Delay cannot be negative.")
            return

        engine_type = self.rules_panel.get_engine_type()
        custom_selectors = self.rules_panel.get_selectors()
        
        config = ScraperConfig(
            url=target_url, engine_type=engine_type, max_pages=max_pages,
            timeout=timeout, custom_selectors=custom_selectors
        )
        
        self._toggle_scrape_controls(active=True)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        for val in self.stats_cards.values():
            val.configure(text="-")
            
        self.scrape_start_time = time.time()
        self.status_dot.configure(fg_color=ACCENT_BLUE)
        self.status_bar_lbl.configure(text="Scraping website...")
        self.status_bar_right.configure(text=f"Engine: {engine_type.upper()} | Starting thread...")
        
        self.scraping_queue = queue.Queue()
        self.active_scraper = ScraperFactory.get_scraper(config)
        
        self.scraping_thread = threading.Thread(
            target=self._scrape_thread_worker, args=(self.active_scraper,), daemon=True
        )
        self.scraping_thread.start()
        self.after(100, self._poll_queue)
        
    def cancel_scraping(self):
        if self.active_scraper:
            self.active_scraper.cancel()
            self.status_bar_lbl.configure(text="Cancelling thread execution...")
            self.cancel_btn.configure(state="disabled")

    def _toggle_scrape_controls(self, active: bool) -> None:
        """Enable or disable scraping controls during active scraping."""
        if active:
            self.scrape_btn.configure(state="disabled", text="Scraping...")
            self.cancel_btn.configure(state="normal")
            self.url_entry.configure(state="disabled")
            self.max_pages_entry.configure(state="disabled")
            self.timeout_entry.configure(state="disabled")
            self.delay_entry.configure(state="disabled")
        else:
            self.scrape_btn.configure(state="normal", text="Start Scraping")
            self.cancel_btn.configure(state="disabled")
            self.url_entry.configure(state="normal")
            self.max_pages_entry.configure(state="normal")
            self.timeout_entry.configure(state="normal")
            self.delay_entry.configure(state="normal")

    def _scrape_thread_worker(self, scraper):
        def progress_cb(current, total, text):
            self.scraping_queue.put({
                "type": "progress", "current": current, "total": total, "text": text
            })
            try:
                delay = self.delay_var.get()
                if delay > 0:
                    time.sleep(delay)
            except Exception:
                pass
        try:
            results = scraper.scrape(progress_callback=progress_cb)
            self.scraping_queue.put({
                "type": "success", "data": results
            })
        except Exception as e:
            logger.exception("Error in scraping thread")
            self.scraping_queue.put({
                "type": "error", "message": str(e)
            })
            
    def _poll_queue(self):
        self.spinner_idx = (self.spinner_idx + 1) % len(SPINNER_FRAMES)
        anim_char = SPINNER_FRAMES[self.spinner_idx]
        
        try:
            while True:
                msg = self.scraping_queue.get_nowait()
                msg_type = msg["type"]
                
                if msg_type == "progress":
                    curr = msg["current"]
                    tot = msg["total"]
                    txt = msg["text"]
                    self.status_bar_lbl.configure(text=f"[{anim_char}] {txt}")
                    self.status_bar_right.configure(text=f"Page: {curr}/{tot} | Active thread running")
                    
                elif msg_type == "success":
                    self.scraped_products = msg["data"]
                    self._on_scrape_completed(success=True)
                    return
                    
                elif msg_type == "error":
                    self._on_scrape_completed(success=False, error_msg=msg["message"])
                    return
                    
                self.scraping_queue.task_done()
        except queue.Empty:
            if self.scraping_thread and self.scraping_thread.is_alive():
                current_status = self.status_bar_lbl.cget("text")
                if current_status.startswith("["):
                    c_idx = current_status.find("]")
                    if c_idx != -1:
                        current_status = current_status[c_idx+1:].strip()
                self.status_bar_lbl.configure(text=f"[{anim_char}] {current_status}")
                
        if self.scraping_thread and self.scraping_thread.is_alive():
            self.after(100, self._poll_queue)
            
    def _on_scrape_completed(self, success: bool, error_msg: Optional[str] = None):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(1.0)
        
        self.scrape_btn.configure(state="normal", text="Start Scraping")
        self.cancel_btn.configure(state="disabled")
        self.url_entry.configure(state="normal")
        
        elapsed = time.time() - self.scrape_start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        
        if success:
            # --- ADVANCED DATA MANAGEMENT: VALIDATION AND DEDUPLICATION ---
            dedup = self.deduplicate_var.get()
            valid_list, invalid_cnt, duplicates_cnt = validate_and_sanitize_products(
                self.scraped_products, deduplicate=dedup
            )
            self.scraped_products = valid_list
            total_count = len(valid_list)
            
            # Auto-save history if enabled
            if self.autosave_var.get() and total_count > 0:
                try:
                    save_session(self.url_entry.get().strip(), self.scraped_products)
                except Exception as e:
                    logger.warning(f"Could not auto-save scraping run: {e}")
            
            # Status messages details
            self.status_dot.configure(fg_color=ACCENT_GREEN)
            msg_status = f"Scrape completed in {mins:02d}:{secs:02d}."
            if duplicates_cnt > 0:
                msg_status += f" {duplicates_cnt} duplicates removed."
            if invalid_cnt > 0:
                msg_status += f" {invalid_cnt} invalid items skipped."
                
            self.status_bar_lbl.configure(text=msg_status)
            self.status_bar_right.configure(text=f"Active dataset: {total_count} products | Idle")
            
            self.results_table.set_data(self.scraped_products)
            self.search_entry.delete(0, 'end')
            self.rating_filter_menu.set("Any")
            self.price_min_entry.delete(0, 'end')
            self.price_max_entry.delete(0, 'end')
            self._update_stats_cards()
            
            self.clear_btn.configure(state="normal")
            if total_count > 0:
                self.export_csv_btn.configure(state="normal")
                self.export_excel_btn.configure(state="normal")
            else:
                messagebox.showinfo(
                    "No Products",
                    "The scraper completed successfully but no valid products were found."
                )
                self.clear_btn.configure(state="disabled")
                self.export_csv_btn.configure(state="disabled")
                self.export_excel_btn.configure(state="disabled")
        else:
            self.status_dot.configure(fg_color=ACCENT_RED)
            self.status_bar_lbl.configure(text="Scraping thread aborted.")
            self.status_bar_right.configure(text="Idle")
            
            self.scraped_products = []
            self.results_table.set_data([])
            self._update_stats_cards()
            self.clear_btn.configure(state="disabled")
            
            messagebox.showerror("Scrape Error", f"An error occurred while scraping:\n{error_msg}")
            
        self.scraping_thread = None
        self.active_scraper = None
        
    def clear_results(self):
        """Wipe dashboard results."""
        self.scraped_products = []
        self.results_table.set_data([])
        self.search_entry.delete(0, 'end')
        self.rating_filter_menu.set("Any")
        self.price_min_entry.delete(0, 'end')
        self.price_max_entry.delete(0, 'end')
        self._update_stats_cards()
        self.clear_btn.configure(state="disabled")
        self.export_csv_btn.configure(state="disabled")
        self.export_excel_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_bar_lbl.configure(text="Results cleared.")
        self.status_bar_right.configure(text="Active dataset: 0 products | Idle")
        
    # ==========================================
    # HISTORY TAB HANDLING
    # ==========================================
    
    def _refresh_history_view(self):
        """Load sessions from JSON and redraw cards in the history tab."""
        for child in self.history_scroll.winfo_children():
            child.destroy()
            
        sessions = get_all_sessions()
        
        if not sessions:
            lbl = ctk.CTkLabel(
                self.history_scroll, text="No previous scraping sessions saved.",
                font=(FONT_FAMILY, 13, "italic"), text_color=TEXT_MUTED
            )
            lbl.pack(pady=40)
            return
            
        for idx, s in enumerate(sessions):
            session_id = s.get("session_id", "")
            url = s.get("url", "")
            timestamp = s.get("timestamp", "")
            count = s.get("products_count", 0)
            
            # Card Container
            card = ctk.CTkFrame(self.history_scroll, fg_color=BG_MAIN, corner_radius=6, border_width=1, border_color=BG_CARD_BORDER)
            card.pack(fill="x", pady=4, padx=5)
            
            # Details block (left)
            details = ctk.CTkFrame(card, fg_color="transparent")
            details.pack(side="left", fill="both", expand=True, padx=12, pady=8)
            
            lbl_url = ctk.CTkLabel(details, text=url, font=(FONT_FAMILY, 12, "bold"), text_color=ACCENT_BLUE, anchor="w")
            lbl_url.pack(fill="x", anchor="w")
            
            lbl_time = ctk.CTkLabel(details, text=f"Ran: {timestamp}  |  Scraped Items: {count}", font=(FONT_FAMILY, 11), text_color=TEXT_SECONDARY, anchor="w")
            lbl_time.pack(fill="x", anchor="w")
            
            # Buttons block (right)
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(side="right", padx=12, pady=8)
            
            btn_load = ctk.CTkButton(
                actions, text="Load Session", font=(FONT_FAMILY, 11, "bold"),
                fg_color=BG_CARD, hover_color=ACCENT_GREEN_HOVER, border_width=1, border_color=BG_CARD_BORDER,
                text_color=TEXT_PRIMARY, width=100, height=26,
                command=lambda data=s.get("products", []), target_url=url: self._load_historic_session(data, target_url)
            )
            btn_load.pack(side="left", padx=4)
            create_tooltip(btn_load, "Reload this scraping run dataset back into the main dashboard table")
            
            btn_del = ctk.CTkButton(
                actions, text="Delete", font=(FONT_FAMILY, 11, "bold"),
                fg_color=BG_CARD, hover_color=ACCENT_RED_HOVER, border_width=1, border_color=BG_CARD_BORDER,
                text_color=TEXT_PRIMARY, width=80, height=26,
                command=lambda sid=session_id: self._delete_historic_session(sid)
            )
            btn_del.pack(side="left", padx=4)
            create_tooltip(btn_del, "Delete this session entry permanently from history logs")
            
    def _load_historic_session(self, products_dicts: List[Dict], target_url: str):
        """Convert dictionaries back to Product objects and populate dashboard."""
        loaded_products = []
        for d in products_dicts:
            loaded_products.append(Product(
                name=d.get("name", "Unknown"),
                price_str=d.get("price_str", "N/A"),
                price_val=d.get("price_val", 0.0),
                rating_val=d.get("rating_val", 0.0),
                rating_str=d.get("rating_str", ""),
                url=d.get("url", ""),
                availability=d.get("availability", "Unknown")
            ))
            
        self.scraped_products = loaded_products
        self.results_table.set_data(loaded_products)
        
        # Prepopulate dashboard URL field
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, target_url)
        
        # Reset filters & recalculate stats
        self.search_entry.delete(0, 'end')
        self.rating_filter_menu.set("Any")
        self.price_min_entry.delete(0, 'end')
        self.price_max_entry.delete(0, 'end')
        self._update_stats_cards()
        
        # Enable controls
        self.clear_btn.configure(state="normal")
        if len(loaded_products) > 0:
            self.export_csv_btn.configure(state="normal")
            self.export_excel_btn.configure(state="normal")
            
        self.status_dot.configure(fg_color=ACCENT_GREEN)
        self.status_bar_lbl.configure(text=f"Loaded session containing {len(loaded_products)} products.")
        self.status_bar_right.configure(text=f"Active dataset: {len(loaded_products)} products | History Loaded")
        
        # Switch to dashboard view
        self.change_view("dashboard")
        messagebox.showinfo("Session Loaded", f"Loaded {len(loaded_products)} products from session history.")
        
    def _delete_historic_session(self, session_id: str):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this scraping session?"):
            try:
                delete_session(session_id)
                self._refresh_history_view()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete session: {e}")
                
    def clear_all_history(self):
        if messagebox.askyesno("Confirm Wipe", "Wipe all saved sessions from history? This cannot be undone."):
            try:
                clear_all_history()
                self._refresh_history_view()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {e}")
                
    # ==========================================
    # EXPORT HANDLERS
    # ==========================================
    
    def _get_export_dataset(self) -> List[Product]:
        """Determine export dataset: checked items only, or all currently filtered items."""
        selected = self.results_table.get_selected_products()
        if selected:
            return selected
        return self.results_table.filtered_products
        
    def export_csv(self):
        export_list = self._get_export_dataset()
        if not export_list:
            messagebox.showwarning("Export Empty", "No products available to export.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV UTF-8", "*.csv"), ("All Files", "*.*")],
            title="Export Results as CSV"
        )
        if not filepath:
            return
            
        try:
            export_to_csv(export_list, filepath)
            messagebox.showinfo("Export Successful", f"Saved {len(export_list)} records to CSV successfully.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write CSV file:\n{e}")
            
    def export_excel(self):
        export_list = self._get_export_dataset()
        if not export_list:
            messagebox.showwarning("Export Empty", "No products available to export.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("All Files", "*.*")],
            title="Export Results as Excel"
        )
        if not filepath:
            return
            
        try:
            export_to_excel(export_list, filepath)
            messagebox.showinfo("Export Successful", f"Saved {len(export_list)} records to Excel successfully.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write Excel file:\n{e}")
