import asyncio
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

async def scrape_betfair():
    async with async_playwright() as p:
        logger.info("Launching chromium for Betfair Exchange...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        target_url = "https://www.betfair.it/exchange/plus/it/calcio-scommesse-1"
        logger.info(f"Navigating to {target_url} (Calcio)...")
        
        try:
            await page.goto(target_url, wait_until="domcontentloaded")
            await asyncio.sleep(5) # Wait for JS to render the matches
            
            # Wiggle mouse
            await page.mouse.move(100, 100)
            
            # Extract match names directly from the DOM framework
            logger.info("Executing DOM Text Extraction...")
            
            # Betfair usually stores team names in spans with class 'name' or 'title' or 'event-name'
            matches = await page.evaluate('''() => {
                const els = document.querySelectorAll('.event-name, .event-title, .name, .team-name');
                return Array.from(els).map(el => el.innerText.replace(/\\n/g, ' - ').trim()).filter(t => t.length > 5);
            }''')
            
            if matches:
                # Deduplicate and clean
                matches = list(dict.fromkeys(matches))
                logger.info(f"✅ Successfully Scraped Live Matches from Betfair Exchange!")
                print("\n" + "="*50)
                print("      BETFAIR EXCHANGE LIVE MATcHES      ")
                print("="*50)
                for i, match in enumerate(matches[:15]):
                    print(f"⚽ {match}")
                print("="*50 + "\n")
            else:
                logger.warning("Could not find specific CSS classes. Dumping raw structural text:")
                raw_text = await page.evaluate("document.body.innerText")
                lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 3]
                for line in lines[20:50]:
                    print(f"| {line}")
                    
            await page.screenshot(path="betfair_success.png", full_page=True)
            logger.info("📸 Saved proof screenshot to betfair_success.png")

        except Exception as e:
            logger.error(f"Error scraping Betfair: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_betfair())
