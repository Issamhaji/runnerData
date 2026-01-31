"""
Data storage and export utilities
"""
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd
import config

logger = logging.getLogger(__name__)


class DataStorage:
    """Handle data storage and export in various formats"""
    
    @staticmethod
    def save_json(data: Any, filepath: Path, indent: int = 2):
        """Save data as JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.info(f"Saved JSON to {filepath}")
        
    @staticmethod
    def load_json(filepath: Path) -> Any:
        """Load JSON data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def flatten_product_data(product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten product data for CSV export
        
        Args:
            product_data: Full product data dictionary
            
        Returns:
            Flattened dictionary suitable for CSV
        """
        flattened = {
            'product_id': product_data.get('product_id'),
            'category_id': product_data.get('category_id'),
            'product_name': product_data.get('product_name', '')
        }
        
        # Extract from initial data
        initial = product_data.get('initial_data', {})
        if initial:
            flattened['description'] = initial.get('description', '')
            
        # Extract from offers
        offers = product_data.get('offers', {})
        if offers and isinstance(offers, dict):
            offers_list = offers.get('offers', [])
            if offers_list:
                # Get best offer (first one)
                best_offer = offers_list[0] if offers_list else {}
                flattened['lowest_price'] = best_offer.get('price', {}).get('amount')
                flattened['lowest_price_currency'] = best_offer.get('price', {}).get('currency')
                flattened['merchant_name'] = best_offer.get('merchant', {}).get('name')
                flattened['total_offers'] = len(offers_list)
        
        # Extract from reviews
        reviews = product_data.get('reviews', {})
        if reviews and isinstance(reviews, dict):
            flattened['average_rating'] = reviews.get('averageRating')
            flattened['total_reviews'] = reviews.get('totalReviews', 0)
            flattened['user_reviews_count'] = len(reviews.get('userReviews', []))
            flattened['pro_reviews_count'] = len(reviews.get('proReviews', []))
        
        # Extract price history summary
        price_history = product_data.get('price_history', {})
        if price_history:
            # Get 3-month history
            three_month = price_history.get('THREE_MONTHS', {})
            if three_month and isinstance(three_month, dict):
                price_points = three_month.get('pricePoints', [])
                if price_points:
                    prices = [p.get('price') for p in price_points if p.get('price')]
                    if prices:
                        flattened['price_history_min_3m'] = min(prices)
                        flattened['price_history_max_3m'] = max(prices)
                        flattened['price_history_avg_3m'] = sum(prices) / len(prices)
        
        # Similar products count
        similar = product_data.get('similar_products', {})
        if similar and isinstance(similar, dict):
            flattened['similar_products_count'] = len(similar.get('products', []))
        
        return flattened
    
    @staticmethod
    def consolidate_products_to_csv(output_file: str = None) -> str:
        """
        Consolidate all product JSON files into a single CSV
        
        Args:
            output_file: Optional output filename
            
        Returns:
            Path to created CSV file
        """
        if output_file is None:
            output_file = Path(config.CONSOLIDATED_OUTPUT_DIR) / "all_products.csv"
        else:
            output_file = Path(output_file)
            
        logger.info("Consolidating products to CSV...")
        
        product_files = list(Path(config.PRODUCT_OUTPUT_DIR).glob("product_*.json"))
        logger.info(f"Found {len(product_files)} product files")
        
        all_products = []
        for product_file in product_files:
            try:
                product_data = DataStorage.load_json(product_file)
                flattened = DataStorage.flatten_product_data(product_data)
                all_products.append(flattened)
            except Exception as e:
                logger.error(f"Error processing {product_file}: {str(e)}")
                continue
        
        # Create DataFrame
        df = pd.DataFrame(all_products)
        
        # Save to CSV
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Saved {len(all_products)} products to {output_file}")
        
        return str(output_file)
    
    @staticmethod
    def consolidate_products_to_json(output_file: str = None) -> str:
        """
        Consolidate all product JSON files into a single JSON array
        
        Args:
            output_file: Optional output filename
            
        Returns:
            Path to created JSON file
        """
        if output_file is None:
            output_file = Path(config.CONSOLIDATED_OUTPUT_DIR) / "all_products.json"
        else:
            output_file = Path(output_file)
            
        logger.info("Consolidating products to JSON...")
        
        product_files = list(Path(config.PRODUCT_OUTPUT_DIR).glob("product_*.json"))
        logger.info(f"Found {len(product_files)} product files")
        
        all_products = []
        for product_file in product_files:
            try:
                product_data = DataStorage.load_json(product_file)
                all_products.append(product_data)
            except Exception as e:
                logger.error(f"Error processing {product_file}: {str(e)}")
                continue
        
        # Save consolidated JSON
        DataStorage.save_json(all_products, output_file)
        logger.info(f"Saved {len(all_products)} products to {output_file}")
        
        return str(output_file)
    
    @staticmethod
    def generate_summary_stats() -> Dict[str, Any]:
        """
        Generate summary statistics from scraped data
        
        Returns:
            Dictionary with summary statistics
        """
        logger.info("Generating summary statistics...")
        
        # Count files
        category_files = list(Path(config.CATEGORY_OUTPUT_DIR).glob("category_*.json"))
        product_files = list(Path(config.PRODUCT_OUTPUT_DIR).glob("product_*.json"))
        
        # Load some sample data
        total_products_in_categories = 0
        categories_info = []
        
        for cat_file in category_files:
            try:
                cat_data = DataStorage.load_json(cat_file)
                total_products_in_categories += cat_data.get('total_products', 0)
                categories_info.append({
                    'id': cat_data.get('category_id'),
                    'name': cat_data.get('category_name'),
                    'products': cat_data.get('total_products', 0)
                })
            except:
                continue
        
        summary = {
            'total_categories': len(category_files),
            'total_products_in_categories': total_products_in_categories,
            'total_product_details_scraped': len(product_files),
            'categories': categories_info
        }
        
        # Save summary
        summary_file = Path(config.CONSOLIDATED_OUTPUT_DIR) / "summary_stats.json"
        DataStorage.save_json(summary, summary_file)
        
        logger.info(f"Summary: {len(category_files)} categories, {len(product_files)} products scraped")
        return summary
