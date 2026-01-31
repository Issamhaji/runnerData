"""
Product scraper - extracts detailed product information
"""
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from tqdm import tqdm
import config
from scraper.api_client import PriceRunnerAPIClient

logger = logging.getLogger(__name__)


class ProductScraper:
    """Scraper for detailed product information"""
    
    def __init__(self, api_client: PriceRunnerAPIClient):
        self.api_client = api_client
        
    async def scrape_product(self, product_id: int, category_id: int, product_name: str = "") -> Optional[Dict[str, Any]]:
        """
        Scrape all details for a single product
        
        Args:
            product_id: Product ID
            category_id: Category ID
            product_name: Optional product name for logging
            
        Returns:
            Dictionary with all product data
        """
        logger.debug(f"Scraping product {product_id} - {product_name}")
        
        product_data = {
            'product_id': product_id,
            'category_id': category_id,
            'product_name': product_name,
            'initial_data': None,
            'offers': None,
            'reviews': None,
            'price_history': {},
            'similar_products': None
        }
        
        try:
            # Get initial product data
            initial_data = await self.api_client.get_product_initial(category_id, product_id)
            product_data['initial_data'] = initial_data
            
            # Get offers and prices
            offers = await self.api_client.get_product_offers(product_id)
            product_data['offers'] = offers
            
            # Get reviews
            reviews = await self.api_client.get_product_reviews(product_id)
            product_data['reviews'] = reviews
            
            # Get price history for different intervals
            for interval in config.PRICE_HISTORY_INTERVALS:
                price_history = await self.api_client.get_price_history(product_id, interval)
                product_data['price_history'][interval] = price_history
            
            # Get similar products
            similar = await self.api_client.get_similar_products(category_id, product_id)
            product_data['similar_products'] = similar
            
            # Save product data
            output_file = Path(config.PRODUCT_OUTPUT_DIR) / f"product_{product_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2, ensure_ascii=False)
            
            # Save raw response if enabled
            if config.SAVE_RAW_RESPONSES:
                raw_file = Path(config.RAW_OUTPUT_DIR) / f"product_{product_id}_raw.json"
                with open(raw_file, 'w', encoding='utf-8') as f:
                    json.dump(product_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Successfully scraped product {product_id}")
            return product_data
            
        except Exception as e:
            logger.error(f"Error scraping product {product_id}: {str(e)}")
            return None
            
    async def scrape_products_from_category(self, category_file: Path) -> List[Dict[str, Any]]:
        """
        Scrape detailed data for all products from a category file
        
        Args:
            category_file: Path to category JSON file
            
        Returns:
            List of product data dictionaries
        """
        logger.info(f"Loading products from {category_file}")
        
        with open(category_file, 'r', encoding='utf-8') as f:
            category_data = json.load(f)
        
        category_id = category_data['category_id']
        products = category_data['products']
        
        logger.info(f"Scraping {len(products)} products from category {category_id}")
        
        results = []
        with tqdm(total=len(products), desc=f"Category {category_id} Products", unit="product") as pbar:
            for product in products:
                try:
                    product_id = product.get('id')
                    product_name = product.get('name', '')
                    
                    if not product_id:
                        logger.warning(f"Product missing ID: {product}")
                        continue
                    
                    # Check if already scraped
                    output_file = Path(config.PRODUCT_OUTPUT_DIR) / f"product_{product_id}.json"
                    if output_file.exists():
                        logger.debug(f"Product {product_id} already scraped, skipping")
                        pbar.update(1)
                        continue
                    
                    product_data = await self.scrape_product(
                        product_id=product_id,
                        category_id=category_id,
                        product_name=product_name
                    )
                    
                    if product_data:
                        results.append(product_data)
                    
                    pbar.update(1)
                    
                except Exception as e:
                    logger.error(f"Error processing product: {str(e)}")
                    pbar.update(1)
                    continue
        
        logger.info(f"Completed scraping {len(results)} products from category {category_id}")
        return results
        
    async def scrape_all_products(self) -> Dict[str, Any]:
        """
        Scrape all products from all category files
        
        Returns:
            Summary statistics
        """
        category_files = list(Path(config.CATEGORY_OUTPUT_DIR).glob("category_*.json"))
        
        logger.info(f"Found {len(category_files)} category files to process")
        
        total_products = 0
        successful_products = 0
        
        for category_file in category_files:
            try:
                results = await self.scrape_products_from_category(category_file)
                total_products += len(results)
                successful_products += len([r for r in results if r is not None])
            except Exception as e:
                logger.error(f"Error processing category file {category_file}: {str(e)}")
                continue
        
        summary = {
            'total_categories': len(category_files),
            'total_products_scraped': successful_products,
            'total_products_attempted': total_products
        }
        
        logger.info(f"Scraping complete: {summary}")
        return summary
