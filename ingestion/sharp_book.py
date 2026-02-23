import logging
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

import os

logger = logging.getLogger(__name__)

class SharpBookAPI:
    def __init__(self):
        self.betfair_base_url = "https://ero.betfair.it/www/sports/exchange/readonly/v1"
        self.pinnacle_base_url = "https://guest.api.pinnacle.com" # Fictional endpoints based on specs
        self.odds_api_key = os.getenv("ODDS_API")
        
        # We reuse the client for connection pooling
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=16), # Waits: 2s, 4s, 8s, 16s...
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        reraise=True
    )
    async def _make_request(self, url: str, headers: dict = None) -> httpx.Response:
        """Helper to make HTTP GET requests with exponential backoff on failures/429s."""
        response = await self.client.get(url, headers=headers)
        
        if response.status_code == 429:
            logger.warning(f"Rate limited (429) on {url}. Tenacity will retry automatically.")
            response.raise_for_status() # Trigger retry
            
        response.raise_for_status()
        return response

    async def fetch_betfair_exchange_odds(self, event_id: str):
        """Fetches matched volumes, Back (Punta) and Lay (Banca) odds from Betfair Exchange."""
        # Note: In a real scenario, proper endpoints are required.
        url = f"{self.betfair_base_url}/bymarket?marketIds={event_id}"
        logger.info(f"Fetching Betfair Exchange odds for {event_id}")
        try:
            response = await self._make_request(url)
            # return response.json()
            # Fictional structured return for design purposes:
            return {
                "source": "Betfair Exchange",
                "market_id": event_id,
                "back_odds": 2.10,
                "lay_odds": 2.12,
                "volume": 15000
            }
        except Exception as e:
            logger.error(f"Failed to fetch Betfair odds: {e}")
            return None

    async def fetch_pinnacle_guest_odds(self, event_id: str):
        """Fetches Fair Odds from Pinnacle's undocumented Mobile Guest APIs."""
        url = f"{self.pinnacle_base_url}/sports/football/events/{event_id}/odds"
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Pro Build/SQ3A.220705.004)",
            "Accept": "application/json"
        }
        logger.info(f"Fetching Pinnacle Fair Odds for {event_id}")
        try:
            response = await self._make_request(url, headers=headers)
            # return response.json()
            return {
                "source": "Pinnacle",
                "market_id": event_id,
                "odds": [1.95, 3.50, 4.20] # 1X2 Example
            }
        except Exception as e:
            logger.error(f"Failed to fetch Pinnacle odds: {e}")
            return None

    async def fetch_from_odds_api(self, sport_key: str = "soccer_italy_serie_a"):
        """Fetches live H2H and Totals odds from Pinnacle and Betfair using The Odds API."""
        if not self.odds_api_key:
            logger.error("ODDS_API key not found in environment.")
            return None
            
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={self.odds_api_key}&regions=eu&markets=h2h,totals&bookmakers=pinnacle,betfair_ex_eu"
        
        logger.info(f"Fetching sharp odds from The Odds API for {sport_key}...")
        try:
            response = await self._make_request(url)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch from The Odds API: {e}")
            return None
