import re
import random
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0"
]

def get_random_headers() -> dict:
    """Return headers with a random User-Agent."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def clean_text(text: Optional[str]) -> str:
    """Clean extra spaces, newlines, and strip text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_price(price_str: Optional[str]) -> Tuple[str, float]:
    """
    Extract display string and numeric float value from a price string.
    e.g., "£51.77" -> ("£51.77", 51.77)
          "45,00 €" -> ("45.00 €", 45.0)
          "none"    -> ("N/A", 0.0)
    """
    if not price_str:
        return "N/A", 0.0

    cleaned = clean_text(price_str)
    # Remove separators like commas between digits if they represent thousands,
    # or handle commas as decimal points (common in Europe).
    # Simple regex to find numbers:
    match = re.search(r'([\d.,]+)', cleaned)
    if not match:
        return cleaned, 0.0

    num_part = match.group(1)
    
    # Try parsing
    try:
        # If there's a comma and a period, e.g., 1,234.56
        if ',' in num_part and '.' in num_part:
            num_val = float(num_part.replace(',', ''))
        # If there's a comma and no period, and it's near the end, e.g. 45,00 -> 45.00
        elif ',' in num_part and len(num_part.split(',')[-1]) <= 2:
            num_val = float(num_part.replace(',', '.'))
        else:
            num_val = float(num_part)
    except ValueError:
        # Fallback extraction of digits and dots only
        digits_only = re.sub(r'[^\d.]', '', num_part.replace(',', '.'))
        try:
            num_val = float(digits_only)
        except ValueError:
            num_val = 0.0

    return cleaned, num_val

def parse_rating(rating_input: Optional[str]) -> Tuple[float, str]:
    """
    Convert verbal rating (e.g., "Three", "one", "5 stars") into float value and stars string.
    e.g., "Three" -> (3.0, "⭐⭐⭐☆☆")
    """
    if not rating_input:
        return 0.0, "☆☆☆☆☆"

    cleaned = clean_text(rating_input).lower()
    
    # Try parsing digits first
    match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
    if match:
        try:
            val = float(match.group(1))
        except ValueError:
            val = 0.0
    else:
        # Word mapping for verbal ratings (common in books.toscrape.com)
        word_to_num = {
            'one': 1.0, 'two': 2.0, 'three': 3.0, 'four': 4.0, 'five': 5.0,
            'first': 1.0, 'second': 2.0, 'third': 3.0, 'fourth': 4.0, 'fifth': 5.0,
        }
        
        val = 0.0
        for word, num in word_to_num.items():
            if word in cleaned:
                val = num
                break

    # Clamp value between 0 and 5
    val = max(0.0, min(5.0, val))
    
    # Generate stars representation
    full_stars = int(val)
    half_star = 1 if (val - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    stars_str = ("⭐" * full_stars) + ("⭐" if half_star else "") + ("☆" * empty_stars)
    return val, stars_str


def resolve_url(base_url: str, relative_url: str) -> str:
    """Resolve a relative URL against a base URL."""
    if not relative_url:
        return base_url
    return urljoin(base_url, relative_url)

def is_valid_url(url: str) -> bool:
    """Check if the provided string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
