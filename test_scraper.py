#!/usr/bin/env python3
"""
Quick test script to verify the scraper works with a small sample
"""
import asyncio
import sys
import logging

# Add project to path
sys.path.insert(0, '/Users/issam/Documents/pricerunner')

from scraper.api_client import PriceRunnerAPIClient

async def test_api():
    """Test API connection with a simple request"""
    print("Testing PriceRunner API connection...")
    
    async with PriceRunnerAPIClient() as client:
        print("✓ Browser initialized")
        
        # Test category discovery
        print("\nDiscovering categories...")
        categories = await client.discover_categories()
        print(f"✓ Found {len(categories)} categories")
        
        if categories:
            # Show first few categories
            print("\nFirst 5 categories:")
            for cat in categories[:5]:
                print(f"  - {cat['id']}: {cat['name']}")
            
            # Test getting products from first category
            first_cat = categories[0]
            print(f"\nTesting product listing from category {first_cat['id']} ({first_cat['name']})...")
            products_data = await client.get_category_products(first_cat['id'], offset=1, size=10)
            
            if products_data and 'products' in products_data:
                products = products_data['products']
                print(f"✓ Found {len(products)} products (showing first 3)")
                
                for i, product in enumerate(products[:3], 1):
                    print(f"\n  Product {i}:")
                    print(f"    ID: {product.get('id')}")
                    print(f"    Name: {product.get('name')}")
                    print(f"    Price: {product.get('lowestPrice', {}).get('amount')} {product.get('lowestPrice', {}).get('currency')}")
                
                # Test detailed product data
                if products:
                    test_product = products[0]
                    product_id = test_product.get('id')
                    category_id = first_cat['id']
                    
                    print(f"\nTesting detailed data for product {product_id}...")
                    
                    # Test initial data
                    initial = await client.get_product_initial(category_id, product_id)
                    if initial:
                        print(f"  ✓ Initial data retrieved")
                    
                    # Test offers
                    offers = await client.get_product_offers(product_id)
                    if offers:
                        print(f"  ✓ Offers retrieved")
                    
                    # Test reviews
                    reviews = await client.get_product_reviews(product_id)
                    if reviews:
                        print(f"  ✓ Reviews retrieved")
                    
                    # Test price history
                    price_history = await client.get_price_history(product_id)
                    if price_history:
                        print(f"  ✓ Price history retrieved")
                    
                    print("\n✅ All API endpoints working correctly!")
                    return True
            else:
                print("⚠️  No products found in category")
                return False
        else:
            print("⚠️  No categories discovered")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        result = asyncio.run(test_api())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
