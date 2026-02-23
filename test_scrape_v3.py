import asyncio
import logging
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

logger = logging.getLogger(__name__)

async def extract_clean_text():
    async with async_playwright() as p:
        logger.info("Launching chromium (HEADED) to bypass blockades...")
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            locale="it-IT",
            timezone_id="Europe/Rome"
        )
        
        page = await context.new_page()
        await stealth_async(page)
        
        target_url = "https://www.bet365.it/#/AS/B1/"
        logger.info(f"Navigating to {target_url} (Calcio/Soccer panel)...")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(4)
            
            # Wiggle mouse and accept GDPR cookies
            await page.mouse.move(100, 100)
            await page.mouse.move(200, 300, steps=10)
            try:
                cookie_btn = await page.wait_for_selector("text='Accetta', text='Accetta tutti', .ccm-CookieConsentPopup_Accept", timeout=5000)
                if cookie_btn:
                    await cookie_btn.click()
            except:
                pass
                
            logger.info("Waiting 8 seconds for JS to stream and render the odds...")
            await asyncio.sleep(8)
            
            # Extract raw text from the DOM body instead of guessing CSS classes
            raw_text = await page.evaluate("document.body.innerText")
            lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 1]
            
            if len(lines) > 20:
                logger.info("✅ Data Successfully Scraped! Structuring output...")
                print("\n" + "="*50)
                print("         LIVE BET365 DATA EXTRACTED       ")
                print("="*50)
                
                # Print a contiguous chunk of lines to show actual teams and odds being parsed
                # Skipping the top navigation bar (about ~15 lines usually)
                for line in lines[20:80]:
                    print(f"➜ {line}")
                    
                print("="*50 + "\n")
            else:
                logger.warning("DOM was loaded, but innerText returned very few lines.")
                print(raw_text)
                await page.screenshot(path="bet365_fallback.png", full_page=True)
            
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(extract_clean_text())
