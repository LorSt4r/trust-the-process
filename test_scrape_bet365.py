import asyncio
import logging
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

logger = logging.getLogger(__name__)

async def scrape_soccer_info():
    async with async_playwright() as p:
        logger.info("Launching chromium (HEADED) masked with stealth...")
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # Using default context for headed mode since custom viewports often flag anti-bots
        context = await browser.new_context(
            locale="it-IT",
            timezone_id="Europe/Rome"
        )
        
        page = await context.new_page()
        await stealth_async(page)
        
        # Targetting the main Homepage
        target_url = "https://www.bet365.it/"
        logger.info(f"Navigating to {target_url} to intercept background XHR data...")
        
        # Build an interceptor to catch the API responses directly instead of parsing HTML
        intercepted_data = []

        async def handle_response(response):
            if "SportsBook.API" in response.url or "sports-configuration" in response.url or "inplay" in response.url:
                try:
                    text = await response.text()
                    if len(text) > 100:
                        intercepted_data.append((response.url, text[:150]))
                except Exception:
                    pass

        page.on("response", handle_response)
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded")
            
            # Wait for initial framework to spin up and fire the XHR requests
            await asyncio.sleep(5)
            
            # Simulate human mouse movement to wake up Bot Protections
            logger.info("Moving mouse dynamically to pass behavioral checks...")
            await page.mouse.move(100, 100)
            await page.mouse.move(200, 300, steps=10)
            await asyncio.sleep(1)
            
            # Scroll to trigger lazy loading API calls
            await page.mouse.wheel(delta_x=0, delta_y=1000)
            await asyncio.sleep(5)
            
            if intercepted_data:
                logger.info(f"✅ Successfully intercepted {len(intercepted_data)} native API payloads!")
                for index, (url, preview) in enumerate(intercepted_data[:10]):
                    print(f"📡 API {index+1}: {url}")
                    print(f"📦 Payload snippet: {preview}...\n")
            else:
                 logger.warning("No sports API payloads intercepted within the timeframe.")
                 await page.screenshot(path="bet365_error.png", full_page=True)
                 logger.info("Saved error screenshot to bet365_error.png")
            
        except Exception as e:
            logger.error(f"Failed to scrape: {e}")
            await page.screenshot(path="bet365_error.png", full_page=True)
            logger.info("Saved error screenshot to bet365_error.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_soccer_info())
