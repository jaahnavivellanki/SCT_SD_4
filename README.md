# Product Scraper Pro

Product Scraper Pro is a desktop application designed to extract product catalog information from e-commerce websites. Built with a modern CustomTkinter GUI, this tool is ideal for portfolio presentations, recruiter reviews, and internship applications.

## Project Overview

Product Scraper Pro provides a professional, user-friendly interface for scraping product details from web storefronts and saving results locally. It supports intelligent scraping engines, data validation, history tracking, and export capabilities for CSV and Excel.

## Features

- ✅ Dashboard statistics for:
  - Total products scraped
  - Average price
  - Highest price
  - Lowest price
- ✅ Scraping history saved locally with timestamp, website URL, and product count
- ✅ Product table search, rating filters, and sorting by name, price, and rating
- ✅ Data management with result clearing, duplicate removal, and validation
- ✅ Export selected or full product lists to CSV and Excel
- ✅ Loading/progress indicator, disabled controls during scraping, and a bottom status bar
- ✅ Error handling for invalid URLs, network failures, empty results, and export issues
- ✅ Modern desktop UI with tooltips and polished navigation

## Technologies Used

- Python 3.14
- CustomTkinter for GUI
- Requests for HTTP requests
- BeautifulSoup4 for HTML parsing
- Pandas and OpenPyXL for export functionality
- JSON for local history storage

## Installation Instructions

1. Clone the repository:

```bash
git clone https://github.com/your-username/ProductScraperPro.git
cd ProductScraperPro
```

2. Create and activate a Python virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows Command Prompt
.\.venv\Scripts\activate.bat
```

3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage Guide

1. Launch the app:

```bash
python run.py
```

2. Enter the target website URL in the dashboard.
3. Configure scraping settings such as page limits, timeout, and polite delay.
4. Start scraping and monitor progress in the status bar.
5. Use the search box, rating filter, and sort headers to refine results.
6. Export selected or all products to CSV/Excel.
7. View saved scraping sessions in the History tab.

## Folder Structure

```text
ProductScraperPro/
├── README.md
├── requirements.txt
├── run.py
├── test_scraper.py
└── src/
    ├── app.py
    ├── gui/
    │   ├── main_window.py
    │   ├── styles.py
    │   └── components/
    │       ├── rules_panel.py
    │       ├── table.py
    │       └── tooltip.py
    ├── scraper/
    │   ├── __init__.py
    │   ├── base.py
    │   └── engines.py
    └── utils/
        ├── exporter.py
        ├── helpers.py
        ├── history.py
        └── validation.py
```

## Screenshots

> Screenshots coming soon. Replace this section with high-quality application snapshots once available.

## Future Enhancements

- Add built-in scheduler to automate recurring scrapes
- Support authenticated scraping and login flows
- Add export to JSON and XML formats
- Implement pagination preview and item selection in the table
- Add dark/light mode switch persistence and user profiles

## Author

**Product Scraper Pro** was built as a portfolio-grade desktop scraping application.

- Author: [Your Name]
- GitHub: `https://github.com/your-username`
- Email: `your.email@example.com`

---

This repository is suitable for GitHub presentation, recruiter review, and internship submissions.