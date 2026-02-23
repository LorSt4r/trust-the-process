import asyncio
import httpx
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_odds_api():
    api_key = os.getenv("ODDS_API")
    if not api_key:
        logger.error("No API key found in .env")
        return
        
    url = f"https://api.the-odds-api.com/v4/sports/soccer_italy_serie_a/odds/?apiKey={api_key}&regions=eu&markets=h2h,totals&bookmakers=pinnacle,betfair_ex_eu"
    
    logger.info(f"Querying The Odds API for Serie A (Pinnacle & Betfair Exchange)...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully fetched {len(data)} matches.")
            if len(data) > 0:
                logger.info("Sample match data:")
                import json
                print(json.dumps(data[0], indent=2))
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_odds_api())
