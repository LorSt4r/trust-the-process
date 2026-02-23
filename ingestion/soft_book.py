import asyncio
import re
import logging
import pytesseract
from io import BytesIO
from PIL import Image
from playwright.async_api import async_playwright, Page, Response

logger = logging.getLogger(__name__)

class SoftBookScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.target_url = "https://www.bet365.it/#/HO/"
        self.intercepted_promos = []

    async def intercept_response(self, response: Response):
        """Callback to inspect XHR/Fetch responses in real time."""
        if response.request.resource_type in ["xhr", "fetch"]:
            try:
                # Bet365 might compress or protect data, but we attempt to read text
                text = await response.text()
                
                # Look for promotional limits using regex
                # Example: "Puntata di €10: vincita di €22"
                match = re.search(r'Puntata\s+di\s+€?(\d+)[.,]?\d*\s*:', text, re.IGNORECASE)
                if match:
                    stake_cap = float(match.group(1))
                    
                    # Assuming we can parse other details, store it temporarily
                    logger.info(f"Intercepted promo with stake cap: €{stake_cap}")
                    self.intercepted_promos.append({
                        "source": "Bet365",
                        "stake_cap": stake_cap,
                        # ... other data would be parsed here from JSON ...
                    })
            except Exception as e:
                pass # Safe to ignore response reading errors (CORS, body missing, etc)

    async def extract_superquotes(self, page: Page):
        """Scrape the visible superquotes using the user's verified DOM text methodology."""
        scraped_matches = []
        try:
            # Replicating the user's logic exactly to parse the live text
            raw_text = await page.evaluate("document.body.innerText")
            lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 2]
            
            # Dump the raw lines to the logger so we can see exactly how Bet365 formats the superquota live
            logger.info("--- RAW DOM TEXT DUMP ---")
            for idx, line in enumerate(lines):
                 if "Fiorentina" in line or "Pisa" in line or "Superquota" in line or "Maggiorata" in line:
                     logger.info(f"Line {idx}: {line}")
                     # Print 2 lines above and 5 lines below for context
                     for j in range(max(0, idx-2), min(len(lines), idx+6)):
                          print(f"[{j}] {lines[j]}")
                     print("-" * 20)
            logger.info("-------------------------")

            # Look for lines containing " v " to identify the match line, then work backwards/forwards
            for i, line in enumerate(lines):
                 if " v " in line and ("Fiorentina" in line or "Pisa" in line):
                     try:
                         # Based on live DOM output:
                         # [145] PIÙ DI 2.5 E SÌ  (Dettaglio)
                         # [146] Totale goal/Entrambe le squadre segnano (Mercato)
                         # [147] Fiorentina v Pisa (Partita)
                         # [148] 2.30 (Quota Normale)
                         # [149] 3.00 (Quota Maggiorata)
                         
                         dettaglio = lines[i-2] if i >= 2 else "N/A"
                         mercato = lines[i-1] if i >= 1 else "N/A"
                         
                         odds_normale = float(lines[i+1].replace(',', '.'))
                         odds_maggiorata = float(lines[i+2].replace(',', '.'))
                         
                         scraped_matches.append({
                             "sport": "Calcio", # Hardcoded for now, could be dynamic
                             "dettaglio": dettaglio,
                             "mercato": mercato,
                             "match": line, # Partita
                             "normal_odds": odds_normale,
                             "soft_odds": odds_maggiorata, 
                             "raw_context": lines[max(0, i-3):min(len(lines), i+6)]
                         })
                     except (IndexError, ValueError) as eval_err:
                         logger.warning(f"Failed to parse odds block around line {i}: {eval_err}")
                         continue

            if not scraped_matches:
                return [{"raw_structure": lines}]
                
        except Exception as e:
            logger.error(f"Text Extraction failed: {e}")
            
        return scraped_matches

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
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
            
            # User's exact stealth bypass string
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {self.target_url}")
            try:
                await page.goto(self.target_url, timeout=60000, wait_until="domcontentloaded")
                
                # Use user's exact wait pattern for DataDome
                await asyncio.sleep(5)
                await page.mouse.move(100, 200)
                await page.mouse.wheel(delta_x=0, delta_y=500)
                await asyncio.sleep(5)
                
                logger.info("Extracting Bet365 Superquotes...")
                matches = await self.extract_superquotes(page)
                if matches:
                    self.intercepted_promos.extend(matches)
                
            except Exception as e:
                logger.error(f"Navigation/Scraping error: {e}")
                
            except Exception as e:
                logger.error(f"Navigation error: {e}")

            await browser.close()
            return self.intercepted_promos

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SoftBookScraper(headless=True)
    asyncio.run(scraper.run())
