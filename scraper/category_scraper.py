"""
Category scraper - discovers categories and extracts product listings
"""
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from tqdm import tqdm
import config
from scraper.api_client import PriceRunnerAPIClient

logger = logging.getLogger(__name__)


class CategoryScraper:
    """Scraper for category discovery and product listing"""
    
    def __init__(self, api_client: PriceRunnerAPIClient):
        self.api_client = api_client
        
    async def discover_all_categories(self) -> List[Dict[str, Any]]:
        """
        Discover all categories from the homepage
        
        Returns:
            List of category dictionaries
        """
        categories = await self.api_client.discover_categories()
        
        # Save categories to file
        output_file = Path(config.CATEGORY_OUTPUT_DIR) / "categories.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(categories)} categories to {output_file}")
        
        return categories
        
    async def scrape_category(self, category_id: int, category_name: str = "") -> Dict[str, Any]:
        """
        Scrape all products from a category
        
        Args:
            category_id: Category ID to scrape
            category_name: Optional category name for logging
            
        Returns:
            Dictionary with category info and all products
        """
        logger.info(f"Scraping category {category_id} - {category_name}")
        
        all_products = []
        offset = 1
        total_hits = None
        
        with tqdm(desc=f"Category {category_id}", unit="products") as pbar:
            while True:
                # Get products for current page
                data = await self.api_client.get_category_products(
                    category_id=category_id,
                    offset=offset,
                    size=config.BATCH_SIZE
                )
                
                if not data:
                    logger.warning(f"No data returned for category {category_id} at offset {offset}")
                    break
                
                # Extract total hits on first request
                if total_hits is None:
                    total_hits = data.get('totalProductHits', 0)
                    pbar.total = total_hits
                    logger.info(f"Category {category_id} has {total_hits} total products")
                
                # Extract products
                products = data.get('products', [])
                if not products:
                    logger.info(f"No more products found at offset {offset}")
                    break
                
                # Add products to list
                all_products.extend(products)
                pbar.update(len(products))
                
                logger.debug(f"Fetched {len(products)} products at offset {offset}")
                
                # Check if we've got all products
                if len(all_products) >= total_hits:
                    break
                    
                # Move to next page
                offset += config.BATCH_SIZE
        
        result = {
            'category_id': category_id,
            'category_name': category_name,
            'total_products': len(all_products),
            'products': all_products
        }
        
        # Save category data
        output_file = Path(config.CATEGORY_OUTPUT_DIR) / f"category_{category_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(all_products)} products from category {category_id} to {output_file}")
        
        # Save raw response if enabled
        if config.SAVE_RAW_RESPONSES:
            raw_file = Path(config.RAW_OUTPUT_DIR) / f"category_{category_id}_raw.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result
        
    async def scrape_all_categories(self, category_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Scrape all categories
        
        Args:
            category_ids: Optional list of category IDs to scrape. If None, discovers all.
            
        Returns:
            List of category results
        """
        # Discover categories if not provided
        if category_ids is None:
            categories = await self.discover_all_categories()
            category_ids = [cat['id'] for cat in categories]
            category_map = {cat['id']: cat['name'] for cat in categories}
        else:
            category_map = {cid: f"Category {cid}" for cid in category_ids}
        
        logger.info(f"Scraping {len(category_ids)} categories...")
        
        results = []
        for category_id in category_ids:
            try:
                result = await self.scrape_category(
                    category_id=category_id,
                    category_name=category_map.get(category_id, "")
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error scraping category {category_id}: {str(e)}")
                continue
        
        logger.info(f"Completed scraping {len(results)} categories")
        return results
