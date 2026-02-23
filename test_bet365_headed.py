import asyncio
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

async def scrape_bet365_headed():
    async with async_playwright() as p:
        logger.info("Launching chromium mimicking user's working configuration...")
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox', 
                '--disable-gpu',
                '--disable-dev-shm-usage', 
                '--window-size=1920,1080'
            ]
        )
        
        context = await browser.new_context(
             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
             viewport={'width': 1920, 'height': 1080}
        )
        
        # User's custom stealth injection instead of playwright-stealth
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        target_url = "https://www.bet365.it/#/HO/"
        logger.info(f"Navigating to {target_url}...")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded")
            logger.info("Waiting 10 seconds to allow DataDome JS challenges to pass...")
            await asyncio.sleep(10)
            
            # Wiggle mouse and click to bypass bot behavioral checks
            await page.mouse.move(500, 500)
            await page.mouse.click(500, 500)
            await asyncio.sleep(2)
            
            await page.mouse.wheel(delta_x=0, delta_y=600)
            await asyncio.sleep(3)
            
            logger.info("Fetching raw DOM text directly...")
            raw_text = await page.evaluate("document.body.innerText")
            lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 3]
            
            if len(lines) > 20:
                print("\n" + "="*50)
                print("         BET365 LIVE DATA SCRAMBLE       ")
                print("="*50)
                
                # We skip the top ~20 lines because they are usually standard bet365 navigation links ('Sport', 'Live', etc.)
                # We want to print the middle sections where the actual matches and numbers populate.
                start_idx = min(25, len(lines)-1)
                for line in lines[start_idx:start_idx+35]:
                    print(f"⚽ {line}")
                    
                print("="*50 + "\n")
                logger.info("✅ Success! Bet365 data verified.")
            else:
                logger.warning("Still blocked. DOM only had a few lines.")
                print(raw_text)
                
            await page.screenshot(path="bet365_headed.png", full_page=True)
            logger.info("📸 Saved screenshot to bet365_headed.png")
            
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_bet365_headed())
