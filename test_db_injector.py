import asyncio
import logging
from datetime import datetime
from db.database import engine, async_session_maker
from db.models import ValueBetting, SportEvent, OpsState, AccountState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def inject_test_data():
    async with async_session_maker() as session:
        # 1. Create a dummy account
        acc = AccountState(
            nome_operatore="TestOperator",
            bankroll_iniziale=1000.00,
            bankroll_corrente=1000.00,
            trust_score=100
        )
        session.add(acc)
        
        # 2. Create a dummy event
        evt = SportEvent(
            data_inizio=datetime.utcnow(),
            sport="Calcio",
            competizione="Serie A",
            squadra_casa="Sassuolo",
            squadra_trasferta="Verona"
        )
        session.add(evt)
        await session.flush() # get evt.id_evento

        # 3. Inject a PENDING Value Bet
        vb = ValueBetting(
            id_evento=evt.id_evento,
            selezione_bet365="D. Berardi Segna",
            quota_giocata=2.50,
            fair_odd_calcolata=2.00,
            expected_value_perc=0.25,
            stake_suggerito=15.00,
            stato_operazione=OpsState.PENDING
        )
        session.add(vb)
        
        await session.commit()
        logger.info("✅ Test data injected! Open Telegram and type /status, then /piazzata 15")

if __name__ == "__main__":
    asyncio.run(inject_test_data())
