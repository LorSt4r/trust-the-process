import asyncio
import logging
from ingestion.sharp_book import SharpBookAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sharp_books():
    logger.info("Initializing Sharp Books API Clients...")
    api = SharpBookAPI()
    
    # Ex: test fetching Betfair Exchange (mock endpoint for logic verification)
    market_id = "1.23456789"
    logger.info("--- Testing Betfair Exchange ---")
    betfair_data = await api.fetch_betfair_exchange_odds(market_id)
    if betfair_data:
        logger.info(f"✅ Betfair Response: {betfair_data}")
    else:
        logger.error("❌ Betfair fetch failed")
        
    # Ex: test fetching Pinnacle (mock endpoint for logic verification)
    event_id = "1564859"
    logger.info("\n--- Testing Pinnacle Guest API ---")
    pinnacle_data = await api.fetch_pinnacle_guest_odds(event_id)
    if pinnacle_data:
        logger.info(f"✅ Pinnacle Response: {pinnacle_data}")
    else:
        logger.error("❌ Pinnacle fetch failed")

    await api.close()

if __name__ == "__main__":
    asyncio.run(test_sharp_books())
