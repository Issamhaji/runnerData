"""
API Client for PriceRunner using Playwright for browser automation
Handles all API requests with proper headers and error handling
"""
import json
import asyncio
import random
import logging
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PriceRunnerAPIClient:
    """API client for PriceRunner with browser automation"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def initialize(self):
        """Initialize browser and context with stealth settings"""
        logger.info("Initializing Playwright browser...")
        self.playwright = await async_playwright().start()
        
        # Launch with arguments to appear more like a real browser
        self.browser = await self.playwright.chromium.launch(
            headless=config.HEADLESS,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',  
                '--no-sandbox',
            ]
        )
        
        # Create context with additional stealth settings
        self.context = await self.browser.new_context(
            user_agent=config.USER_AGENT,
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'application/json, text/plain, */*',
            }
        )
        
        # Hide webdriver property
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")
        
    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
        
    async def _delay(self):
        """Random delay between requests"""
        delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)
        
    async def _make_request(self, url: str, retries: int = 0) -> Optional[Dict[str, Any]]:
        """
        Make a request to the API and return JSON response
        
        Args:
            url: Full URL to request
            retries: Current retry count
            
        Returns:
            JSON response as dict or None if failed
        """
        try:
            logger.debug(f"Requesting: {url}")
            
            # Navigate to URL and wait for content
            response = await self.page.goto(url, timeout=config.BROWSER_TIMEOUT, wait_until="load")
            
            # Check status
            if response and response.status == 403:
                logger.warning(f"403 Forbidden - may need to handle cookies/captcha")
                return None
            
            # Wait for content to be available
            await asyncio.sleep(1.0)
            
            # Try to get content from pre tag (API responses are typically in <pre>)
            try:
                # Wait for pre tag to appear
                await self.page.wait_for_selector('pre', timeout=5000, state='attached')
                
                # Get the text content
                pre_element = await self.page.query_selector('pre')
                if pre_element:
                    json_text = await pre_element.text_content()
                    
                    if json_text and len(json_text.strip()) > 0:
                        try:
                            data = json.loads(json_text)
                            logger.debug(f"Successfully parsed JSON ({len(json_text)} chars)")
                            return data
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {str(e)}")
                            logger.debug(f"Content preview: {json_text[:200]}")
                            return None
                    else:
                        logger.error(f"Pre tag found but content is empty")
                        return None
                else:
                    logger.error(f"No pre element found")
                    return None
                    
            except asyncio.TimeoutError:
                # If pre tag not found, try body as fallback
                logger.warning(f"Pre tag not found, trying body")
                try:
                    body_element = await self.page.query_selector('body')
                    if body_element:
                        json_text = await body_element.text_content()
                        if json_text and len(json_text.strip()) > 0:
                            try:
                                data = json.loads(json_text.strip())
                                logger.debug(f"Successfully parsed JSON from body ({len(json_text)} chars)")
                                return data
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error from body: {str(e)}")
                                # Log page content to understand what we're getting
                                html = await self.page.content()
                                logger.debug(f"Page HTML preview: {html[:500]}")
                                return None
                        else:
                            logger.error(f"Body found but content is empty")
                            return None
                    else:
                        logger.error(f"No body element found")
                        return None
                except Exception as e:
                    logger.error(f"Error reading body: {str(e)}")
                    return None
                
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            
            if retries < config.MAX_RETRIES:
                logger.info(f"Retrying... (attempt {retries + 1}/{config.MAX_RETRIES})")
                await self._delay()
                return await self._make_request(url, retries + 1)
            else:
                logger.error(f"Max retries reached for {url}")
                return None
                
    async def get_category_products(self, category_id: int, offset: int = 1, size: int = 100) -> Optional[Dict[str, Any]]:
        """
        Get products from a category
        
        Args:
            category_id: Category ID
            offset: Offset for pagination (must be >= 1)
            size: Number of products per page
            
        Returns:
            JSON response with products list
        """
        url = f"{config.SEARCH_API}/category/v4/{config.LOCALE}/{category_id}?size={size}&offset={offset}"
        data = await self._make_request(url)
        await self._delay()
        return data
        
    async def get_product_initial(self, category_id: int, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get initial product data
        
        Args:
            category_id: Category ID
            product_id: Product ID
            
        Returns:
            JSON response with product initial data
        """
        url = f"{config.PRODUCT_DETAIL_API}/v0/initial/{config.LOCALE}/{category_id}/{product_id}"
        data = await self._make_request(url)
        await self._delay()
        return data
        
    async def get_product_offers(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get product offers and prices
        
        Args:
            product_id: Product ID
            
        Returns:
            JSON response with offers
        """
        url = (f"{config.PRODUCT_DETAIL_API}/v0/offers/{config.LOCALE}/{product_id}"
               f"?af_ORIGIN=NATIONAL&af_ITEM_CONDITION=NEW,UNKNOWN&sortByPreset=RECOMMENDED")
        data = await self._make_request(url)
        await self._delay()
        return data
        
    async def get_product_reviews(self, product_id: int, limit_user: int = 100, limit_pro: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get product reviews
        
        Args:
            product_id: Product ID
            limit_user: Number of user reviews to fetch
            limit_pro: Number of professional reviews to fetch
            
        Returns:
            JSON response with reviews
        """
        url = (f"{config.REVIEW_API}/overview/{config.LOCALE}/{product_id}/"
               f"?limitUser={limit_user}&limitPro={limit_pro}&lang=en")
        data = await self._make_request(url)
        await self._delay()
        return data
        
    async def get_price_history(self, product_id: int, interval: str = "THREE_MONTHS") -> Optional[Dict[str, Any]]:
        """
        Get product price history
        
        Args:
            product_id: Product ID
            interval: Time interval (THREE_MONTHS, SIX_MONTHS, ONE_YEAR)
            
        Returns:
            JSON response with price history
        """
        url = (f"{config.PRICE_HISTORY_API}/product/{product_id}/{config.LOCALE}/"
               f"{config.PRICE_HISTORY_GRANULARITY}?merchantId=&selectedInterval={interval}&filter=NATIONAL")
        data = await self._make_request(url)
        await self._delay()
        return data
        
    async def get_similar_products(self, category_id: int, product_id: int, size: int = 20) -> Optional[Dict[str, Any]]:
        """
        Get similar products
        
        Args:
            category_id: Category ID
            product_id: Product ID
            size: Number of similar products
            
        Returns:
            JSON response with similar products
        """
        url = f"{config.SIMILAR_API}/{config.LOCALE}/{category_id}/{product_id}?size={size}"
        data = await self._make_request(url)
        await self._delay()
        return data
        
    async def discover_categories(self) -> List[Dict[str, Any]]:
        """
        Discover all categories from the homepage
        
        Returns:
            List of category dictionaries with id, name, and URL
        """
        logger.info("Discovering categories from homepage...")
        
        try:
            # Navigate to homepage
            await self.page.goto(config.BASE_URL, timeout=config.BROWSER_TIMEOUT, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # Give page time to fully load
            
            # Accept cookies if present - try multiple selectors
            try:
                # Try to execute JavaScript to click any cookie consent buttons
                cookie_closed = await self.page.evaluate("""
                    () => {
                        const cookieSelectors = [
                            'button[id*="cookie"]',
                            'button[class*="cookie"]',
                            'button[id*="consent"]',
                            '#onetrust-accept-btn-handler',
                            '.qc-cmp2-summary-buttons button:last-child'
                        ];
                        for (const selector of cookieSelectors) {
                            const btn = document.querySelector(selector);
                            if (btn && btn.offsetParent !== null) {
                                btn.click();
                                console.log('Clicked cookie button:', selector);
                                return true;
                            }
                        }
                        // Also try text-based selectors
                        const buttons = Array.from(document.querySelectorAll('button'));
                        for (const btn of buttons) {
                            const text = btn.innerText.toLowerCase();
                            if (text.includes('accept') || text.includes('agree')) {
                                btn.click();
                                console.log('Clicked button with text:', btn.innerText);
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                if cookie_closed:
                    logger.info("Cookie consent closed")
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"No cookie consent found: {str(e)}")
            
            # Try to open menu to see all categories
            try:
                menu_opened = await self.page.evaluate("""
                    () => {
                        // Try multiple menu button selectors
                        const menuSelectors = [
                            'button[aria-label="Open menu"]',
                            'button[aria-label*="menu" i]',
                            'button[class*="menu" i]:not([aria-label="Close menu"])',
                            'button:has-text("Menu")',
                            '[data-testid*="menu"]'
                        ];
                        
                        for (const selector of menuSelectors) {
                            try {
                                const el = document.querySelector(selector);
                                if (el && el.offsetParent !== null) {
                                    el.click();
                                    console.log('Clicked menu with selector:', selector);
                                    return true;
                                }
                            } catch (e) {
                                continue;
                            }
                        }
                        
                        // Try to find any button that might be a menu
                        const buttons = Array.from(document.querySelectorAll('button'));
                        for (const btn of buttons) {
                            const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                            const className = (btn.className || '').toLowerCase();
                            if (ariaLabel.includes('menu') || ariaLabel.includes('navigation')) {
                                btn.click();
                                console.log('Clicked menu button via aria-label');
                                return true;
                            }
                        }
                        
                        return false;
                    }
                """)
                
                if menu_opened:
                    logger.info("Menu opened successfully")
                    await asyncio.sleep(3)  # Wait for menu to fully expand
                else:
                    logger.warning("Could not find menu button - will try to extract categories from current page")
            except Exception as e:
                logger.warning(f"Error opening menu: {str(e)} - continuing anyway")
            
            # Extract category links - try with and without menu being open
            categories = []
            seen_ids = set()  # Track seen IDs to avoid duplicates
            
            # Use JavaScript to extract all category links
            category_data = await self.page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="/cl/"]'));
                    console.log('Found ' + links.length + ' category links');
                    return links.map(link => ({
                        href: link.getAttribute('href'),
                        text: link.innerText.trim()
                    })).filter(item => item.href && item.text && item.text.length > 0);
                }
            """)
            
            logger.info(f"Found {len(category_data)} category links")
            
            for item in category_data:
                try:
                    href = item['href']
                    text = item['text']
                    
                    # Extract category ID from URL
                    # Format is /cl/{id}/{name} or /cl/{id}-{name}
                    parts = href.split('/cl/')
                    if len(parts) > 1:
                        # Get the part after /cl/
                        remainder = parts[1]
                        # Split by either / or - to get the ID
                        if '/' in remainder:
                            cat_id_str = remainder.split('/')[0]
                        elif '-' in remainder:
                            cat_id_str = remainder.split('-')[0]
                        else:
                            cat_id_str = remainder
                        
                        try:
                            cat_id = int(cat_id_str)
                            
                            # Avoid duplicates
                            if cat_id not in seen_ids:
                                seen_ids.add(cat_id)
                                full_url = f"{config.BASE_URL}{href}" if not href.startswith('http') else href
                                categories.append({
                                    'id': cat_id,
                                    'name': text,
                                    'url': full_url
                                })
                                logger.debug(f"Found category: {cat_id} - {text}")
                        except ValueError:
                            logger.debug(f"Could not parse ID from: {cat_id_str}")
                            continue
                except Exception as e:
                    logger.debug(f"Error extracting category data: {str(e)}")
                    continue
            
            logger.info(f"Discovered {len(categories)} unique categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error discovering categories: {str(e)}")
            return []
