import asyncio
import logging
from engine.calculator import Calculator
from ingestion.soft_book import SoftBookScraper
from db.database import init_db, async_session_maker
from db.models import SportEvent, ValueBetting, OpsState
from datetime import datetime, timezone
import os
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipeline():
    await init_db()
    
    print("\n" + "="*50)
    print("      🚀 INITIATING FULL E2E PIPELINE RUN       ")
    print("="*50)
    
    logger.info("Step 1: Ingesting Data from Bet365 via Stealth Chromium...")
    scraper = SoftBookScraper(headless=False)
    bet365_data = await scraper.run()
    
    # Try to find the exact Match in the live extracted data
    fiorentina_bet = None
    if bet365_data:
        for item in bet365_data:
            if "match" in item and ("Fiorentina" in item['match'] or "Pisa" in item['match']):
                fiorentina_bet = item
                break

    if not fiorentina_bet:
        logger.error("PIPELINE FAILED: Could not find Fiorentina natively in the live feed!")
        return
        
    logger.info(f"Successfully identified live Superquota organically from DOM: {fiorentina_bet['match']} @ {fiorentina_bet['soft_odds']}")

    logger.info("Step 2: Querying Sharp Book (Exchange) for Lay Odds...")
    from ingestion.sharp_book import SharpBookAPI
    sharp_api = SharpBookAPI()
    odds_data = await sharp_api.fetch_from_odds_api()
    await sharp_api.close()
    
    exchange_match = "N/D"
    exchange_market = "N/D"
    lay_odds = 0.0
    back_odds = 0.0
    
    if odds_data:
        for match in odds_data:
            # Simple fallback match logic for the live test
            if "Fiorentina" in match.get("home_team", "") or "Pisa" in match.get("away_team", ""):
                exchange_match = f"{match['home_team']} v {match['away_team']} (Betfair)"
                
                for bookie in match.get("bookmakers", []):
                    if bookie["key"] == "betfair_ex_eu":
                        for market in bookie.get("markets", []):
                            if market["key"] == "h2h":
                                for outcome in market["outcomes"]:
                                    if outcome["name"] == "Fiorentina":
                                        back_odds = outcome["price"]
                            if market["key"] == "h2h_lay":
                                for outcome in market["outcomes"]:
                                    if outcome["name"] == "Fiorentina":
                                        lay_odds = outcome["price"]
                
                exchange_market = "Esito Finale 1 (Fiorentina)"
                break
                
    if lay_odds == 0.0:
        logger.warning("Market not found on Exchange. Falling back to trigger manual recalculation warning.")
    
    logger.info("Step 3: Crunching Math and Expected Value (EV)...")
    if lay_odds > 0:
        odds_list = [back_odds, lay_odds] 
        true_prob = Calculator.devig_multiplicative(odds_list)[0] 
        fair_odd = 1.0 / true_prob
    else:
        fair_odd = 1.0 # placeholder to avoid div by zero if missing
    
    ev = Calculator.calculate_ev(fiorentina_bet['soft_odds'], fair_odd)
    logger.info(f"Fair Odd: {fair_odd:.2f} | EV: {ev*100:.2f}%")
    
    if ev > 0.02: 
        bankroll = 1000.0 
        kelly_stake = Calculator.apply_kelly_criterion(
            promo_odd=fiorentina_bet['soft_odds'],
            fair_odd=fair_odd,
            bankroll=bankroll,
            fractional_multiplier=0.25,
            promo_cap=10.0 
        )
        
        logger.info("Step 4: Pushing organically scraped State to Database...")
        async with async_session_maker() as session:
            evento = SportEvent(
                data_inizio=datetime.now(timezone.utc),
                sport=fiorentina_bet['sport'],
                competizione="Serie B",
                squadra_casa="Fiorentina",
                squadra_trasferta="Pisa"
            )
            session.add(evento)
            await session.flush() # flush to get the id_evento
            
            vb = ValueBetting(
                id_evento=evento.id_evento,
                selezione_bet365=fiorentina_bet['match'],
                dettaglio=fiorentina_bet['dettaglio'],
                mercato=fiorentina_bet['mercato'],
                quota_normale=fiorentina_bet['normal_odds'],
                quota_giocata=fiorentina_bet['soft_odds'],
                fair_odd_calcolata=fair_odd,
                expected_value_perc=ev*100,
                stake_suggerito=kelly_stake,
                stato_operazione=OpsState.PENDING
            )
            session.add(vb)
            await session.commit()
            logger.info("Successfully persisted +EV Opportunity to Database.")
        
        logger.info("Step 5: Dispatching Telegram Alert...")
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        
        # Parse the chat IDs if it's stored as comma-separated or single
        chat_ids_env = os.getenv("TELEGRAM_CHAT_IDS", "")
        # fallback to single chat id if set
        if not chat_ids_env:
            chat_ids_env = os.getenv("TELEGRAM_CHAT_ID", "") 
            
        chat_ids = [cid.strip() for cid in chat_ids_env.split(",") if cid.strip()]
        
    if ev > 0.02:
        # Check against "Market Not Found" scenario logic
        if lay_odds <= 1.01:
            exchange_msg = "❌ Mercato non trovato sull'Exchange."
            ev_msg = "N/D"
            kelly_msg = "0.00"
            footer = "Usa `/ricalcola [QuotaBet365] [Lay] [Back]` se trovi il mercato manualmente."
        else:
            exchange_msg = f"📉 Exchange Lay Riferimento: {lay_odds}\n📊 Exchange Back Riferimento: {back_odds}"
            ev_msg = f"+{ev*100:.2f}%"
            kelly_msg = f"€{kelly_stake:.2f}"
            footer = f"❓ Verifica RapidFuzz: Controlla che le partite corrispondano.\n\nPer confermare l'ingresso, rispondi con: `/piazzata {kelly_stake:.2f}`\n_(Se il mercato è errato, usa `/ricalcola`)_"
            
        msg = (
            f"✨ NUOVA Superquota Bet365 ✨\n\n"
            f"⚽ Sport: {fiorentina_bet['sport']}\n"
            f"📝 Dettaglio: {fiorentina_bet['dettaglio']}\n"
            f"🆚 Partita: {fiorentina_bet['match']}\n"
            f"📊 Mercato: {fiorentina_bet['mercato']}\n"
            f"📉 Quota Normale: {str(fiorentina_bet['normal_odds']).replace('.', ',')}\n"
            f"📈 Quota Maggiorata: {str(fiorentina_bet['soft_odds']).replace('.', ',')}\n\n"
            f"🏛️ **Sharp Book (Betfair)**\n"
            f"🆚 Partita Exchange: {exchange_match}\n"
            f"📊 Mercato Exchange: {exchange_market}\n"
            f"{exchange_msg}\n\n"
            f"🔥 Valore Atteso (EV) Reale: {ev_msg}\n"
            f"⚖️ Stake Kelly Consigliato: {kelly_msg}\n\n"
            f"{footer}"
        )
        print("\n" + msg + "\n")
        
        if telegram_token and chat_ids:
            try:
                bot = Bot(token=telegram_token)
                for chat_id in chat_ids:
                    await bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
                logger.info("Real Telegram message dispatched successfully!")
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
        else:
            logger.warning("TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not found in .env. Real message not sent via API.")
    else:
        logger.info("No actionable +EV found (EV < 2%).")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
