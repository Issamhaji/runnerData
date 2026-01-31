#!/usr/bin/env python3
"""
Debug script to see what the API is actually returning
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Test URL
        url = "https://www.pricerunner.com/uk/api/search-edge-rest/public/search/category/v4/UK/19?size=10&offset=1"
        
        print(f"Loading: {url}")
        response = await page.goto(url, wait_until="domcontentloaded")
        print(f"Status: {response.status}")
        
        await asyncio.sleep(2)
        
        # Get all content types
        content = await page.content()
        print(f"\nHTML Content length: {len(content)}")
        print("=" * 80)
        print(content[:1000])
        print("=" * 80)
        
        # Try to get JSON 
        result = await page.evaluate("""
            () => {
                const body = document.querySelector('body');
                const pre = document.querySelector('pre');
                
                return {
                    hasBody: !!body,
                    hasPre: !!pre,
                    bodyText: body ? body.innerText.substring(0, 500) : null,
                    preText: pre ? pre.innerText.substring(0, 500) : null,
                    htmlBodyText: body ? body.textContent.substring(0, 500) : null
                };
            }
        """)
        
        print("\nJavaScript evaluation results:")
        for key, value in result.items():
            print(f"{key}: {value}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_api())
