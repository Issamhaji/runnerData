#!/usr/bin/env python3
"""
PriceRunner Scraper - Main execution script
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path
import config
from scraper.api_client import PriceRunnerAPIClient
from scraper.category_scraper import CategoryScraper
from scraper.product_scraper import ProductScraper
from scraper.data_storage import DataStorage

logger = logging.getLogger(__name__)


async def scrape_categories(api_client: PriceRunnerAPIClient, category_ids: list = None):
    """Scrape category listings"""
    logger.info("=== Stage 1: Scraping Category Listings ===")
    category_scraper = CategoryScraper(api_client)
    
    if category_ids:
        results = await category_scraper.scrape_all_categories(category_ids)
    else:
        results = await category_scraper.scrape_all_categories()
    
    logger.info(f"Completed category scraping: {len(results)} categories processed")
    return results


async def scrape_products(api_client: PriceRunnerAPIClient):
    """Scrape detailed product information"""
    logger.info("=== Stage 2: Scraping Product Details ===")
    product_scraper = ProductScraper(api_client)
    summary = await product_scraper.scrape_all_products()
    logger.info(f"Completed product scraping: {summary}")
    return summary


def consolidate_data():
    """Consolidate scraped data into final formats"""
    logger.info("=== Stage 3: Consolidating Data ===")
    
    # Generate summary statistics
    stats = DataStorage.generate_summary_stats()
    logger.info(f"Summary stats: {stats}")
    
    # Export to requested formats
    if config.OUTPUT_FORMAT in ['json', 'both']:
        json_file = DataStorage.consolidate_products_to_json()
        logger.info(f"Consolidated JSON: {json_file}")
    
    if config.OUTPUT_FORMAT in ['csv', 'both']:
        csv_file = DataStorage.consolidate_products_to_csv()
        logger.info(f"Consolidated CSV: {csv_file}")
    
    logger.info("Data consolidation complete!")


async def main_async(args):
    """Main async execution flow"""
    logger.info("Starting PriceRunner scraper...")
    logger.info(f"Configuration: Categories={args.categories}, Mode={args.mode}")
    
    # Initialize API client
    async with PriceRunnerAPIClient() as api_client:
        
        # Stage 1: Category scraping
        if args.mode in ['full', 'categories']:
            category_ids = args.categories if args.categories else config.CATEGORY_IDS
            await scrape_categories(api_client, category_ids)
        
        # Stage 2: Product scraping
        if args.mode in ['full', 'products']:
            await scrape_products(api_client)
    
    # Stage 3: Data consolidation
    if args.mode in ['full', 'consolidate']:
        consolidate_data()
    
    logger.info("Scraping complete!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='PriceRunner Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all categories and products
  python main.py --mode full
  
  # Scrape specific categories only
  python main.py --mode categories --categories 10 94 82
  
  # Scrape products only (requires category data)
  python main.py --mode products
  
  # Consolidate existing data
  python main.py --mode consolidate
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'categories', 'products', 'consolidate'],
        default='full',
        help='Scraping mode (default: full)'
    )
    
    parser.add_argument(
        '--categories',
        type=int,
        nargs='+',
        help='Specific category IDs to scrape (default: all)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        default=config.HEADLESS,
        help='Run browser in headless mode'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.LOG_LEVEL,
        help=f'Logging level (default: {config.LOG_LEVEL})'
    )
    
    args = parser.parse_args()
    
    # Update config based on args
    config.HEADLESS = args.headless
    config.LOG_LEVEL = args.log_level
    
    # Update logging level
    logging.getLogger().setLevel(getattr(logging, config.LOG_LEVEL))
    
    try:
        # Run async main
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
