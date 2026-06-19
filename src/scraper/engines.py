import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Callable

from src.scraper.base import BaseScraper, Product, ScraperConfig
from src.utils.helpers import (
    get_random_headers,
    clean_text,
    parse_price,
    parse_rating,
    resolve_url
)

logger = logging.getLogger(__name__)

class BooksToScrapeEngine(BaseScraper):
    """
    Dedicated scraper engine for http://books.toscrape.com
    Handles multi-page pagination.
    """
    def scrape(self, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[Product]:
        products = []
        current_url = self.config.url
        current_page = 1
        max_pages = self.config.max_pages
        
        session = requests.Session()
        session.headers.update(self.config.headers or get_random_headers())
        
        # Determine total pages if not strictly bounded
        # For simplicity, we loop up to max_pages or until no next button.
        while current_page <= max_pages and current_url:
            if self._is_cancelled:
                logger.info("Scraping cancelled by user.")
                break
                
            if progress_callback:
                progress_callback(current_page, max_pages, f"Fetching page {current_page}...")
                
            try:
                response = session.get(current_url, timeout=self.config.timeout)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Error fetching {current_url}: {e}")
                raise RuntimeError(f"Failed to fetch page {current_page}: {str(e)}")
                
            soup = BeautifulSoup(response.content, 'html.parser')
            pods = soup.select('article.product_pod')
            
            if not pods:
                logger.warning(f"No products found on page {current_page} ({current_url})")
                break
                
            page_products = []
            for pod in pods:
                if self._is_cancelled:
                    break
                    
                # Name
                name_el = pod.select_one('h3 > a')
                name = name_el.get('title') or name_el.text if name_el else "Unknown Product"
                name = clean_text(name)
                
                # URL
                relative_link = name_el.get('href') if name_el else ""
                prod_url = resolve_url(current_url, relative_link)
                
                # Price
                price_el = pod.select_one('p.price_color')
                price_str = price_el.text if price_el else ""
                disp_price, val_price = parse_price(price_str)
                
                # Rating
                rating_el = pod.select_one('p.star-rating')
                rating_class = ""
                if rating_el:
                    # e.g., ['star-rating', 'Three']
                    classes = rating_el.get('class', [])
                    rating_class = next((c for c in classes if c != 'star-rating'), "")
                val_rating, disp_rating = parse_rating(rating_class)
                
                # Availability
                avail_el = pod.select_one('p.instock.availability')
                availability = clean_text(avail_el.text) if avail_el else "Unknown"
                
                product = Product(
                    name=name,
                    price_str=disp_price,
                    price_val=val_price,
                    rating_val=val_rating,
                    rating_str=disp_rating,
                    url=prod_url,
                    availability=availability
                )
                page_products.append(product)
                
            products.extend(page_products)
            
            if progress_callback:
                progress_callback(
                    current_page, 
                    max_pages, 
                    f"Page {current_page} scraped. Found {len(page_products)} products."
                )
            
            # Find next page
            next_button = soup.select_one('li.next > a')
            if next_button and current_page < max_pages:
                next_href = next_button.get('href')
                current_url = resolve_url(current_url, next_href)
                current_page += 1
            else:
                break
                
        return products

class JSONLDEngine(BaseScraper):
    """
    General e-commerce scraper that attempts to parse application/ld+json metadata.
    This works on thousands of Shopify, WooCommerce, Magento, etc. e-commerce websites.
    """
    def scrape(self, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[Product]:
        products = []
        url = self.config.url
        max_pages = self.config.max_pages
        
        session = requests.Session()
        session.headers.update(self.config.headers or get_random_headers())
        
        if progress_callback:
            progress_callback(1, max_pages, "Analyzing page for structured JSON-LD data...")
            
        try:
            response = session.get(url, timeout=self.config.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch target URL: {str(e)}")
            
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        
        for script in scripts:
            if self._is_cancelled:
                break
            try:
                data = json.loads(script.string or '')
            except (json.JSONDecodeError, TypeError):
                continue
                
            # Helper to recursively search for Product object
            def extract_products(obj) -> List[Dict]:
                results = []
                if isinstance(obj, dict):
                    if obj.get('@type') == 'Product':
                        results.append(obj)
                    else:
                        for k, v in obj.items():
                            results.extend(extract_products(v))
                elif isinstance(obj, list):
                    for item in obj:
                        results.extend(extract_products(item))
                return results
                
            found_products = extract_products(data)
            
            for fp in found_products:
                if self._is_cancelled:
                    break
                name = clean_text(fp.get('name', 'Unknown Product'))
                prod_url = resolve_url(url, fp.get('url', ''))
                
                # Extract price & availability from Offers
                offers = fp.get('offers', {})
                price_str = ""
                avail_str = "Unknown"
                
                if isinstance(offers, dict):
                    price = offers.get('price')
                    currency = offers.get('priceCurrency', '$')
                    if price:
                        price_str = f"{currency}{price}" if str(price).startswith(('$', '€', '£')) else f"{price} {currency}"
                    
                    avail = offers.get('availability', '')
                    if 'InStock' in avail or 'in_stock' in avail:
                        avail_str = "In Stock"
                    elif 'OutOfStock' in avail or 'out_of_stock' in avail:
                        avail_str = "Out of Stock"
                    elif avail:
                        avail_str = clean_text(avail.split('/')[-1])  # Extract last path segment of Schema URL
                elif isinstance(offers, list) and len(offers) > 0:
                    first_offer = offers[0]
                    price = first_offer.get('price')
                    currency = first_offer.get('priceCurrency', '$')
                    if price:
                        price_str = f"{price} {currency}"
                    avail = first_offer.get('availability', '')
                    if 'InStock' in avail:
                        avail_str = "In Stock"
                        
                disp_price, val_price = parse_price(price_str)
                
                # Extract rating
                aggregate_rating = fp.get('aggregateRating', {})
                rating_str = ""
                if isinstance(aggregate_rating, dict):
                    rating_val = aggregate_rating.get('ratingValue')
                    if rating_val:
                        rating_str = str(rating_val)
                val_rating, disp_rating = parse_rating(rating_str)
                
                products.append(Product(
                    name=name,
                    price_str=disp_price,
                    price_val=val_price,
                    rating_val=val_rating,
                    rating_str=disp_rating,
                    url=prod_url or url,
                    availability=avail_str
                ))
                
        # If no JSON-LD products, search standard metadata tags (meta og:product)
        if not products:
            if progress_callback:
                progress_callback(1, max_pages, "No JSON-LD metadata found. Checking OpenGraph meta tags...")
            
            # Simple metadata extraction fallback
            og_title = soup.find('meta', property='og:title')
            og_price = soup.find('meta', property='product:price:amount')
            og_currency = soup.find('meta', property='product:price:currency')
            og_avail = soup.find('meta', property='product:availability')
            
            if og_title:
                name = og_title.get('content', '')
                price_amt = og_price.get('content', '') if og_price else ''
                price_curr = og_currency.get('content', '$') if og_currency else ''
                price_str = f"{price_curr}{price_amt}" if price_amt else ""
                disp_price, val_price = parse_price(price_str)
                
                avail = og_avail.get('content', '') if og_avail else 'Unknown'
                avail_str = "In Stock" if 'instock' in avail.lower() or 'in stock' in avail.lower() else "Unknown"
                
                products.append(Product(
                    name=clean_text(name),
                    price_str=disp_price,
                    price_val=val_price,
                    rating_val=0.0,
                    rating_str="☆☆☆☆☆",
                    url=url,
                    availability=avail_str
                ))
                
        if progress_callback:
            progress_callback(1, 1, f"Meta scrape finished. Found {len(products)} products.")
            
        return products

class CustomCSSEngine(BaseScraper):
    """
    Parser that uses user-defined CSS selectors to extract product items.
    """
    def scrape(self, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[Product]:
        products = []
        current_url = self.config.url
        current_page = 1
        max_pages = self.config.max_pages
        
        selectors = self.config.custom_selectors or {}
        container_sel = selectors.get('container', '').strip()
        name_sel = selectors.get('name', '').strip()
        price_sel = selectors.get('price', '').strip()
        rating_sel = selectors.get('rating', '').strip()
        url_sel = selectors.get('url', '').strip()
        avail_sel = selectors.get('availability', '').strip()
        next_sel = selectors.get('next_page', '').strip()
        
        if not container_sel:
            raise ValueError("Product Container CSS selector is required for custom scraping.")
            
        session = requests.Session()
        session.headers.update(self.config.headers or get_random_headers())
        
        while current_page <= max_pages and current_url:
            if self._is_cancelled:
                break
                
            if progress_callback:
                progress_callback(current_page, max_pages, f"Fetching custom page {current_page}...")
                
            try:
                response = session.get(current_url, timeout=self.config.timeout)
                response.raise_for_status()
            except requests.RequestException as e:
                raise RuntimeError(f"Failed to fetch page {current_page}: {str(e)}")
                
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select(container_sel)
            
            if not items:
                logger.warning(f"No elements matched container selector '{container_sel}' on page {current_page}")
                break
                
            page_products = []
            for item in items:
                if self._is_cancelled:
                    break
                    
                # Name
                name = "Unknown Product"
                if name_sel:
                    el = item.select_one(name_sel)
                    if el:
                        name = el.get('title') or el.text
                else:
                    # Fallback to first heading or bold text
                    el = item.select_one('h1, h2, h3, h4, h5, strong')
                    if el:
                        name = el.text
                name = clean_text(name)
                
                # Product URL
                prod_url = current_url
                if url_sel:
                    el = item.select_one(url_sel)
                    if el:
                        # check if href attribute exists
                        relative = el.get('href', '')
                        prod_url = resolve_url(current_url, relative)
                else:
                    # Fallback to first link inside container
                    el = item.select_one('a')
                    if el:
                        prod_url = resolve_url(current_url, el.get('href', ''))
                        
                # Price
                price_str = ""
                if price_sel:
                    el = item.select_one(price_sel)
                    if el:
                        price_str = el.text
                disp_price, val_price = parse_price(price_str)
                
                # Rating
                rating_str = ""
                if rating_sel:
                    el = item.select_one(rating_sel)
                    if el:
                        # Try title attribute, class names, or text
                        rating_str = el.get('title') or el.get('data-rating') or el.text
                val_rating, disp_rating = parse_rating(rating_str)
                
                # Availability
                avail_str = "Unknown"
                if avail_sel:
                    el = item.select_one(avail_sel)
                    if el:
                        avail_str = el.text
                avail_str = clean_text(avail_str)
                
                product = Product(
                    name=name,
                    price_str=disp_price,
                    price_val=val_price,
                    rating_val=val_rating,
                    rating_str=disp_rating,
                    url=prod_url,
                    availability=avail_str
                )
                page_products.append(product)
                
            products.extend(page_products)
            
            if progress_callback:
                progress_callback(
                    current_page, 
                    max_pages, 
                    f"Page {current_page} scraped. Found {len(page_products)} products."
                )
                
            # Next page check
            if next_sel and current_page < max_pages:
                next_btn = soup.select_one(next_sel)
                if next_btn and next_btn.get('href'):
                    current_url = resolve_url(current_url, next_btn.get('href'))
                    current_page += 1
                else:
                    break
            else:
                break
                
        return products

class ScraperFactory:
    """Factory to create the appropriate scraper engine."""
    @staticmethod
    def get_scraper(config: ScraperConfig) -> BaseScraper:
        url_lower = config.url.lower()
        
        if config.engine_type == "books_to_scrape" or "books.toscrape.com" in url_lower:
            return BooksToScrapeEngine(config)
        elif config.engine_type == "custom_css" and config.custom_selectors:
            return CustomCSSEngine(config)
        elif config.engine_type == "autodetect":
            # Check url, default to JSON-LD first
            return JSONLDEngine(config)
        else:
            # Fallback
            return JSONLDEngine(config)
