import dataclasses
from typing import List, Dict, Optional, Callable

@dataclasses.dataclass
class Product:
    name: str
    price_str: str
    price_val: float  # Numeric value for filtering/sorting
    rating_val: float  # Numeric rating (0.0 to 5.0) for filtering/sorting
    rating_str: str  # Display rating (e.g., "⭐⭐⭐☆☆" or "3/5")
    url: str
    availability: str  # "In Stock", "Out of Stock", etc.

@dataclasses.dataclass
class ScraperConfig:
    url: str
    engine_type: str = "autodetect"  # "autodetect", "books_to_scrape", "custom_css"
    max_pages: int = 1
    timeout: int = 10
    custom_selectors: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None

class BaseScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self._is_cancelled = False

    def scrape(self, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[Product]:
        """
        Scrape product details.
        
        :param progress_callback: Callable[[current_page, total_pages, status_text], None]
        :return: List of scraped products
        """
        raise NotImplementedError("Subclasses must implement scrape()")

    def cancel(self):
        """Cancel the scraping operation."""
        self._is_cancelled = True
