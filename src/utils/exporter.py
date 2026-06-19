import logging
from typing import List
import pandas as pd

from src.scraper.base import Product

logger = logging.getLogger(__name__)

def products_to_dataframe(products: List[Product]) -> pd.DataFrame:
    """Convert a list of Product objects into a pandas DataFrame."""
    rows = []
    for product in products:
        rows.append({
            "Product Name": product.name,
            "Price": product.price_str,
            "Numeric Price": product.price_val,
            "Rating": product.rating_str,
            "Numeric Rating": product.rating_val,
            "Availability Status": product.availability,
            "Product URL": product.url,
        })
    return pd.DataFrame(rows)

def export_to_csv(products: List[Product], filepath: str) -> None:
    """Export the provided products to a CSV file."""
    if not products:
        raise ValueError("No products to export.")

    try:
        df = products_to_dataframe(products)
        df_export = df.drop(columns=["Numeric Price", "Numeric Rating"])
        df_export.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(
            f"Successfully exported {len(products)} products to CSV: {filepath}"
        )
    except Exception as exc:
        logger.error(f"Failed to export to CSV: {exc}")
        raise RuntimeError(f"CSV Export failed: {exc}") from exc

def export_to_excel(products: List[Product], filepath: str) -> None:
    """Export the provided products to an Excel workbook."""
    if not products:
        raise ValueError("No products to export.")

    try:
        df = products_to_dataframe(products)
        df_export = df.drop(columns=["Numeric Price", "Numeric Rating"])

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df_export.to_excel(writer, sheet_name="Scraped Products", index=False)
            worksheet = writer.sheets["Scraped Products"]
            for col in worksheet.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    value = str(cell.value or "")
                    if len(value) > max_len:
                        max_len = len(value)
                worksheet.column_dimensions[col_letter].width = min(max_len + 3, 50)

        logger.info(
            f"Successfully exported {len(products)} products to Excel: {filepath}"
        )
    except Exception as exc:
        logger.error(f"Failed to export to Excel: {exc}")
        raise RuntimeError(f"Excel Export failed: {exc}") from exc
