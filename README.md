# PriceRunner Web Scraper

A comprehensive web scraper for PriceRunner that extracts product data including details, prices, reviews, price history, and features.

## Features

- 🔍 **Category Discovery**: Automatically discovers all product categories
- 📦 **Product Listing**: Extracts all products from categories with pagination
- 📊 **Detailed Data**: Scrapes comprehensive product information:
  - Product details and specifications
  - All store offers and prices
  - User and professional reviews
  - Price history (multiple time intervals)
  - Similar products
- 💾 **Multiple Output Formats**: Export data as JSON and/or CSV
- 🤖 **Browser Automation**: Uses Playwright to bypass API restrictions
- ⚡ **Rate Limiting**: Built-in delays to avoid being blocked
- 📈 **Progress Tracking**: Real-time progress bars and logging

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/issam/Documents/pricerunner
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

## Usage

### Quick Start

Scrape all categories and products:
```bash
python main.py --mode full
```

### Scraping Modes

**1. Full Scrape** (recommended for first run):
```bash
python main.py --mode full
```
This will:
- Discover all categories
- Extract all product listings
- Scrape detailed data for each product
- Consolidate data into final output files

**2. Categories Only**:
```bash
python main.py --mode categories
```
Only scrapes category listings and product IDs.

**3. Specific Categories**:
```bash
python main.py --mode categories --categories 10 94 82
```
Scrape only specific category IDs (e.g., 10=Landline Phones, 94=Headphones).

**4. Products Only**:
```bash
python main.py --mode products
```
Scrapes detailed product data (requires category data to exist).

**5. Consolidate Only**:
```bash
python main.py --mode consolidate
```
Only consolidates existing scraped data into final output files.

### Advanced Options

```bash
# Run with visible browser (for debugging)
python main.py --mode full --headless=False

# Increase logging verbosity
python main.py --mode full --log-level DEBUG
```

## Configuration

Edit `config.py` to customize:

- **Country/Region**: Change `COUNTRY_CODE` and `LOCALE` for different PriceRunner regions
- **Rate Limiting**: Adjust `MIN_DELAY` and `MAX_DELAY` between requests
- **Output Format**: Set `OUTPUT_FORMAT` to "json", "csv", or "both"
- **Price History**: Configure time intervals in `PRICE_HISTORY_INTERVALS`
- **Categories**: Set specific `CATEGORY_IDS` or leave `None` to discover all

## Output Structure

```
data/
├── categories/
│   ├── categories.json          # All discovered categories
│   ├── category_10.json         # Products in category 10
│   └── category_94.json         # Products in category 94
├── products/
│   ├── product_123456.json      # Detailed data for product 123456
│   └── product_789012.json      # Detailed data for product 789012
├── consolidated/
│   ├── all_products.json        # All products in single JSON file
│   ├── all_products.csv         # All products in CSV format
│   └── summary_stats.json       # Summary statistics
└── raw/
    └── *_raw.json               # Raw API responses (if enabled)
```

## Data Fields

### Product CSV/JSON includes:

- **Basic Info**: product_id, category_id, product_name, description
- **Pricing**: lowest_price, lowest_price_currency, merchant_name, total_offers
- **Reviews**: average_rating, total_reviews, user_reviews_count, pro_reviews_count
- **Price History**: min/max/avg prices over 3 months
- **Related**: similar_products_count

### Full JSON includes:

- Complete API responses for all endpoints
- Detailed offer information from all merchants
- Full review text and ratings
- Complete price history data
- Product specifications and features

## API Endpoints Used

The scraper uses the following PriceRunner API endpoints:

1. **Category Listing**: `/api/search-edge-rest/public/search/category/v4/`
2. **Product Initial Data**: `/api/product-detail-edge-rest/public/product-detail/v0/initial/`
3. **Product Offers**: `/api/product-detail-edge-rest/public/product-detail/v0/offers/`
4. **Reviews**: `/api/review-edge-rest/public/v2/products/reviews/overview/`
5. **Price History**: `/api/product-information-edge-rest/public/pricehistory/product/`
6. **Similar Products**: `/api/similar-edge-rest/public/search/products/similar/`

## Technical Details

- **Browser Automation**: Playwright with Chromium
- **Rate Limiting**: 2-5 second delays between requests (configurable)
- **Error Handling**: Automatic retries with exponential backoff
- **Pagination**: Handles category pagination automatically
- **Resumability**: Skips already-scraped products

## Troubleshooting

### 403 Forbidden Errors
The scraper uses Playwright to bypass this, but if you still get errors:
- Try increasing delays in `config.py`
- Run with `--headless=False` to see what's happening
- Check if PriceRunner changed their structure

### Browser Not Found
Run: `playwright install chromium`

### Slow Scraping
This is expected due to rate limiting. To speed up:
- Reduce `MIN_DELAY` and `MAX_DELAY` (risk of being blocked)
- Scrape specific categories only

### Out of Memory
Large scrapes can use significant memory:
- Scrape categories in batches
- Disable `SAVE_RAW_RESPONSES` in config

## Example Workflow

```bash
# Step 1: Discover and scrape categories only
python main.py --mode categories

# Step 2: Review the categories.json file and pick specific ones
# Edit config.py to set CATEGORY_IDS = [10, 94]

# Step 3: Scrape products from those categories
python main.py --mode products

# Step 4: Consolidate into final output
python main.py --mode consolidate

# View results
open data/consolidated/all_products.csv
```

## License

This scraper is for educational and research purposes. Please respect PriceRunner's terms of service and robots.txt. Use responsibly and don't overload their servers.

## Support

For issues or questions, check:
- Configuration in `config.py`
- Logs in `scraper.log`
- Debug mode: `python main.py --log-level DEBUG`
