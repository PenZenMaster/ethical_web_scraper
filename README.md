# Ethical Web Scraper

A Playwright-powered web scraping tool designed to ethically extract permitted HTML content for reuse, such as for distributors like OHD Joliet republishing product content from Overhead Door.

## Features
- JavaScript-rendered scraping via Playwright
- Targeted section scraping using CSS selectors
- Image link preservation and normalization
- Outputs clean JSON for CMS/WordPress import

## Usage
```bash
python main.py scrape "<URL>" --selector "<CSS_SELECTOR>"
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
playwright install
```