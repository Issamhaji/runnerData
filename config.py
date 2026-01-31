"""
Configuration settings for PriceRunner scraper
"""
import os
from typing import List, Optional

# Base URLs
BASE_URL = "https://www.pricerunner.com"
COUNTRY_CODE = "uk"  # Can be changed to other countries (us, se, de, etc.)
LOCALE = "UK"

# API Endpoints
API_BASE = f"{BASE_URL}/{COUNTRY_CODE}/api"
SEARCH_API = f"{API_BASE}/search-edge-rest/public/search"
PRODUCT_DETAIL_API = f"{API_BASE}/product-detail-edge-rest/public/product-detail"
REVIEW_API = f"{API_BASE}/review-edge-rest/public/v2/products/reviews"
PRICE_HISTORY_API = f"{API_BASE}/product-information-edge-rest/public/pricehistory"
SIMILAR_API = f"{API_BASE}/similar-edge-rest/public/search/products/similar"

# Scraping Settings
BATCH_SIZE = 100  # Products per page
MIN_DELAY = 2  # Minimum delay between requests (seconds)
MAX_DELAY = 5  # Maximum delay between requests (seconds)
MAX_RETRIES = 3  # Maximum number of retries for failed requests
TIMEOUT = 30  # Request timeout in seconds

# Category Settings - Set specific category IDs or leave empty to discover all
# Example: CATEGORY_IDS = [10, 94, 82]  # Landline Phones, Headphones, Smartphones
CATEGORY_IDS: Optional[List[int]] = None  # None = scrape all categories

# Price History Settings
PRICE_HISTORY_INTERVALS = ["THREE_MONTHS", "SIX_MONTHS", "ONE_YEAR"]
PRICE_HISTORY_GRANULARITY = "DAY"  # Can be DAY, WEEK, MONTH

# Output Settings
OUTPUT_DIR = "data"
CATEGORY_OUTPUT_DIR = f"{OUTPUT_DIR}/categories"
PRODUCT_OUTPUT_DIR = f"{OUTPUT_DIR}/products"
CONSOLIDATED_OUTPUT_DIR = f"{OUTPUT_DIR}/consolidated"
RAW_OUTPUT_DIR = f"{OUTPUT_DIR}/raw"  # For raw API responses

# Output formats: json, csv, both
OUTPUT_FORMAT = "both"
SAVE_RAW_RESPONSES = True  # Save raw API responses for debugging

# Browser Settings
HEADLESS = True  # Run browser in headless mode
BROWSER_TIMEOUT = 30000  # Browser timeout in milliseconds
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "scraper.log"

# Create output directories
for directory in [OUTPUT_DIR, CATEGORY_OUTPUT_DIR, PRODUCT_OUTPUT_DIR, 
                  CONSOLIDATED_OUTPUT_DIR, RAW_OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)
