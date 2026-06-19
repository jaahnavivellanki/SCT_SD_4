import os
import unittest
from src.scraper import ScraperConfig, ScraperFactory, Product
from src.utils.helpers import clean_text, parse_price, parse_rating, resolve_url
from src.utils.exporter import export_to_csv, export_to_excel
from src.utils.validation import validate_and_sanitize_products
from src.utils.history import save_session, get_all_sessions, delete_session

class TestHelpers(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(clean_text("  hello \n world   "), "hello world")
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_parse_price(self):
        # Normal prices
        self.assertEqual(parse_price("£51.77"), ("£51.77", 51.77))
        self.assertEqual(parse_price("$29.99"), ("$29.99", 29.99))
        # European format
        self.assertEqual(parse_price("45,00 €")[1], 45.0)
        # Empty/missing
        self.assertEqual(parse_price("")[1], 0.0)

    def test_parse_rating(self):
        # Verbal ratings
        self.assertEqual(parse_rating("Three"), (3.0, "⭐⭐⭐☆☆"))
        self.assertEqual(parse_rating("Five"), (5.0, "⭐⭐⭐⭐⭐"))
        self.assertEqual(parse_rating("star-rating One"), (1.0, "⭐☆☆☆☆"))
        # Numeric / fallback ratings
        self.assertEqual(parse_rating("4.5 stars"), (4.5, "⭐⭐⭐⭐⭐"))
        # Missing
        self.assertEqual(parse_rating("")[1], "☆☆☆☆☆")

    def test_resolve_url(self):
        base = "http://books.toscrape.com/catalogue/category/index.html"
        rel = "../book-title/index.html"
        self.assertEqual(resolve_url(base, rel), "http://books.toscrape.com/catalogue/book-title/index.html")

class TestScrapingAndExport(unittest.TestCase):
    def test_books_to_scrape(self):
        print("\n--- Running Live Integration Test with books.toscrape.com ---")
        config = ScraperConfig(
            url="http://books.toscrape.com/",
            engine_type="books_to_scrape",
            max_pages=1,
            timeout=10
        )
        
        scraper = ScraperFactory.get_scraper(config)
        
        def progress_cb(current, total, status):
            print(f"Progress: Page {current}/{total} - {status}")
            
        try:
            products = scraper.scrape(progress_callback=progress_cb)
            print(f"Scrape completed successfully. Total products found: {len(products)}")
            
            # Assertions
            self.assertGreater(len(products), 0, "No products were scraped.")
            
            # Check fields
            first = products[0]
            print("First product details:")
            print(f"  Name: {first.name}")
            print(f"  Price: {first.price_str} (Val: {first.price_val})")
            print(f"  Rating: {first.rating_str} (Val: {first.rating_val})")
            print(f"  Availability: {first.availability}")
            print(f"  URL: {first.url}")
            
            self.assertTrue(len(first.name) > 0, "Name is empty")
            self.assertTrue(first.price_val > 0.0, "Price is 0.0 or negative")
            self.assertTrue(first.rating_val > 0.0, "Rating is 0.0 or negative")
            self.assertTrue(first.url.startswith("http"), "URL does not start with http")
            self.assertTrue(len(first.availability) > 0, "Availability is empty")
            
            # Test exporting
            csv_path = "test_export.csv"
            excel_path = "test_export.xlsx"
            
            # Export CSV
            export_to_csv(products, csv_path)
            self.assertTrue(os.path.exists(csv_path), "CSV file was not created.")
            os.remove(csv_path)
            
            # Export Excel
            export_to_excel(products, excel_path)
            self.assertTrue(os.path.exists(excel_path), "Excel file was not created.")
            os.remove(excel_path)
            
            print("Export tests completed successfully.")
            
        except Exception as e:
            self.fail(f"Scraping failed with exception: {e}")

class TestDataManagement(unittest.TestCase):
    def test_validation_and_deduplication(self):
        # Create mock products list containing duplicates and invalid entries
        products = [
            Product("Product A", "$10.00", 10.0, 4.0, "⭐⭐⭐⭐☆", "http://example.com/a", "In Stock"),
            Product("Product A", "$10.00", 10.0, 4.0, "⭐⭐⭐⭐☆", "http://example.com/a", "In Stock"), # Duplicate URL
            Product("   ", "$15.00", 15.0, 3.0, "⭐⭐⭐☆☆", "http://example.com/b", "In Stock"), # Missing/blank Name
            Product("Product C", "$20.00", -5.0, 6.0, "⭐⭐⭐⭐⭐", "invalid_url", "In Stock"), # Invalid URL
            Product("Product D", "$25.00", 25.0, 2.0, "⭐⭐☆☆☆", "https://example.com/d", "") # Valid URL, empty Availability
        ]
        
        valid_list, invalid_cnt, duplicates_cnt = validate_and_sanitize_products(products, deduplicate=True)
        
        # We expect Product A (deduplicated), Product D (valid, sanitized).
        # Discarded: Product A (duplicate URL), blank name, Product C (invalid URL).
        self.assertEqual(len(valid_list), 2)
        self.assertEqual(invalid_cnt, 2) # blank name & invalid URL
        self.assertEqual(duplicates_cnt, 1) # duplicate Product A
        
        self.assertEqual(valid_list[0].name, "Product A")
        self.assertEqual(valid_list[1].name, "Product D")
        self.assertEqual(valid_list[1].availability, "Unknown") # Sanitized from ""

    def test_history_logging(self):
        test_file = "test_history.json"
        if os.path.exists(test_file):
            os.remove(test_file)
            
        products = [
            Product("Book 1", "£12.50", 12.5, 4.0, "⭐⭐⭐⭐☆", "http://books/1", "In Stock"),
            Product("Book 2", "£15.99", 15.99, 5.0, "⭐⭐⭐⭐⭐", "http://books/2", "Out of Stock")
        ]
        
        # Save session
        sid = save_session("http://books.toscrape.com", products, filepath=test_file)
        self.assertTrue(len(sid) > 0)
        
        # Load sessions
        sessions = get_all_sessions(filepath=test_file)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["products_count"], 2)
        self.assertEqual(sessions[0]["products"][0]["name"], "Book 1")
        
        # Delete session
        delete_session(sid, filepath=test_file)
        sessions = get_all_sessions(filepath=test_file)
        self.assertEqual(len(sessions), 0)
        
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    unittest.main()
