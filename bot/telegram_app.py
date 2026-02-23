import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from decimal import Decimal

from db.database import engine, async_session_maker
from db.models import ValueBetting, AccountState, MugBet, OpsState, MugType
from sqlalchemy import select, update, desc
from engine.calculator import Calculator

load_dotenv()
logger = logging.getLogger(__name__)

# Basic Telegram Handlers for OpSec and State Machine
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cyborg Bot Online. Listening for Superquotes.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns a dashboard of the current Account State."""
    async with async_session_maker() as session:
        stmt = select(AccountState).limit(1)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            await update.message.reply_text("Nessun account trovato.")
            return

        msg = (
            f"📊 **STATUS ACCOUNT**\n"
            f"Operatore: {account.nome_operatore}\n"
            f"Bankroll Iniziale: €{account.bankroll_iniziale}\n"
            f"Bankroll Corrente: €{account.bankroll_corrente}\n"
            f"Trust Score: {account.trust_score}/100"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

async def piazzata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirms the latest PENDING Value Bet."""
    try:
        try:
            amount_str = context.args[0].replace(',', '.')
            amount = Decimal(amount_str)
        except (IndexError, ValueError, TypeError):
            await update.message.reply_text("Uso: /piazzata [importo]")
            return

        async with async_session_maker() as session:
            # Find latest pending vb
            stmt = select(ValueBetting).where(
                ValueBetting.stato_operazione == OpsState.PENDING
            ).order_by(desc(ValueBetting.timestamp_alert)).limit(1)
            
            result = await session.execute(stmt)
            vb = result.scalar_one_or_none()
            
            if not vb:
                await update.message.reply_text("Nessuna Superquota PENDING trovata.")
                return
                
            vb.stato_operazione = OpsState.PIAZZATA
            vb.stake_effettivo = amount
            
            # Threat model: Reduce trust score since it's a +EV bet
            stmt_acc = select(AccountState).limit(1)
            acc_result = await session.execute(stmt_acc)
            account = acc_result.scalar_one_or_none()
            if account:
                account.trust_score = max(0, account.trust_score - 10)
                account.bankroll_corrente -= amount # Deduct stake for now
            
            msg = f"✅ Confermata scommessa da €{amount}. Trust Score aggiornato a {account.trust_score if account else 'N/A'}."
            
            # OpSec Proactive Threshold Warning
            if account and account.trust_score < 40:
                msg += "\n⚠️ **ATTENZIONE OPSEC:** Il tuo Trust Score è sceso sotto 40. Piazza una /mug bet (Cover Bet) il prima possibile per evitare la profilazione del conto da parte di Bet365!"
                
            await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Errore /piazzata: {e}")
        await update.message.reply_text(f"Ops, c'è stato un errore: {e}")

async def scartata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Marks the latest PENDING Value Bet as rejected/discarded."""
    async with async_session_maker() as session:
        stmt = select(ValueBetting).where(
            ValueBetting.stato_operazione == OpsState.PENDING
        ).order_by(desc(ValueBetting.timestamp_alert)).limit(1)
        
        result = await session.execute(stmt)
        vb = result.scalar_one_or_none()
        
        if not vb:
            await update.message.reply_text("Nessuna Superquota in attesa da scartare.")
            return
            
        vb.stato_operazione = OpsState.SCARTATA
        await session.commit()
        await update.message.reply_text("❌ Operazione scartata e storicizzata.")

async def mug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registers a Mug Bet to increase Trust Score."""
    try:
        try:
            amount_str = context.args[0].replace(',', '.')
            amount = Decimal(amount_str)
        except (IndexError, ValueError, TypeError):
            await update.message.reply_text("Uso: /mug [costo_qualificante]")
            return
            
        async with async_session_maker() as session:
            stmt_acc = select(AccountState).limit(1)
            acc_result = await session.execute(stmt_acc)
            account = acc_result.scalar_one_or_none()
            
            if account:
                # OpSec: Mug bets increase trust score
                account.trust_score = min(100, account.trust_score + 15)
                # Deduct the qualifying loss from the bankroll
                account.bankroll_corrente -= amount
                await session.commit()
                
                await update.message.reply_text(f"🛡️ Mug Bet registrata (Costo: €{amount}). Trust Score salito a {account.trust_score}.")
            else:
                 await update.message.reply_text("Errore DB: Nessun account trovato.")
    except Exception as e:
        logger.error(f"Errore /mug: {e}")
        await update.message.reply_text(f"Ops, c'è stato un errore: {e}")

async def ricalcola(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually calculates EV and Stake if the bot missed the Exchange Market."""
    try:
        # Expected format: /ricalcola [QuotaBet365] [QuotaLay] [QuotaBack]
        if len(context.args) < 3:
            await update.message.reply_text("Uso: /ricalcola [QuotaBet365] [QuotaLay] [QuotaBack]\nEsempio: /ricalcola 3.0 2.15 2.05")
            return
            
        q_bet365 = float(context.args[0].replace(',', '.'))
        q_lay = float(context.args[1].replace(',', '.'))
        q_back = float(context.args[2].replace(',', '.'))
        
        # Calculate Fair Odd
        odds_list = [q_back, q_lay]
        true_prob = Calculator.devig_multiplicative(odds_list)[0]
        fair_odd = 1.0 / true_prob
        
        # Calculate EV
        ev = Calculator.calculate_ev(q_bet365, fair_odd)
        
        # Calculate Stake (assuming a simulated 1000 bankroll or fetching from DB)
        async with async_session_maker() as session:
            stmt = select(AccountState).limit(1)
            result = await session.execute(stmt)
            account = result.scalar_one_or_none()
            bankroll = float(account.bankroll_corrente) if account else 1000.0
            
        kelly_stake = Calculator.apply_kelly_criterion(
            promo_odd=q_bet365,
            fair_odd=fair_odd,
            bankroll=bankroll,
            fractional_multiplier=0.25,
            promo_cap=10.0
        )
        
        msg = (
            f"🔄 **RICALCOLO MANUALE** 🔄\n\n"
            f"📈 Bet365: {q_bet365}\n"
            f"📉 Exchange Lay/Back: {q_lay}/{q_back}\n"
            f"⚖️ Fair Odd (De-vigged): {fair_odd:.2f}\n"
            f"🔥 **Valore Atteso (EV)**: {ev*100:.2f}%\n"
            f"💰 **Stake Suggerito (Kelly)**: €{kelly_stake:.2f}\n\n"
        )
        
        if ev > 0.02:
            msg += f"✅ EV Positivo. Puoi forzare l'ingresso usando:\n`/piazzata {kelly_stake:.2f}`"
        else:
            msg += f"❌ EV Negativo/Basso. Sconsigliato."
            
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Errore /ricalcola: {e}")
        await update.message.reply_text(f"Ops, c'è stato un errore: {e}")

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN missing in .env")
        return
        
        app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("piazzata", piazzata))
    app.add_handler(CommandHandler("scartata", scartata))
    app.add_handler(CommandHandler("mug", mug))
    app.add_handler(CommandHandler("ricalcola", ricalcola))

    logger.info("Starting Telegram Bot...")
    app.run_polling()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
