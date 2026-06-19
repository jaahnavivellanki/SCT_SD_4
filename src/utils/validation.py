import logging
from typing import List, Tuple, Set

from src.scraper.base import Product
from src.utils.helpers import is_valid_url

logger = logging.getLogger(__name__)

def validate_and_sanitize_products(
    products: List[Product],
    deduplicate: bool = True
) -> Tuple[List[Product], int, int]:
    """
    Validate scraped products and remove duplicates/invalid entries.

    :param products: Raw list of parsed Product dataclasses.
    :param deduplicate: If True, remove duplicate items by product URL.
    :return: A tuple of (validated_products_list, invalid_count, duplicates_removed_count)
    """
    validated: List[Product] = []
    seen_urls: Set[str] = set()

    invalid_count = 0
    duplicates_count = 0

    for p in products:
        # --- 1. DATA VALIDATION ---
        # Rule A: Name must exist and not be empty
        name = p.name.strip()
        if not name or name.lower() == "unknown product":
            logger.warning(f"Discarding invalid item: missing/unknown name. URL: {p.url}")
            invalid_count += 1
            continue

        # Rule B: URL must be valid protocol
        if not p.url or not is_valid_url(p.url):
            logger.warning(f"Discarding invalid item: incorrect URL format: '{p.url}'")
            invalid_count += 1
            continue

        # Rule C: Sanitize values
        price_val = max(0.0, p.price_val)
        rating_val = max(0.0, min(5.0, p.rating_val))

        sanitized_product = Product(
            name=name,
            price_str=p.price_str,
            price_val=price_val,
            rating_val=rating_val,
            rating_str=p.rating_str,
            url=p.url,
            availability=p.availability or "Unknown"
        )

        # --- 2. DUPLICATE DETECTION ---
        # We index by product URL to check duplicates
        url_key = sanitized_product.url.lower().strip()
        if deduplicate and url_key in seen_urls:
            duplicates_count += 1
            logger.info(f"Duplicate product detected and removed: '{sanitized_product.name}' ({sanitized_product.url})")
            continue

        seen_urls.add(url_key)
        validated.append(sanitized_product)

    return validated, invalid_count, duplicates_count
