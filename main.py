import asyncio
import logging
from db.database import init_db
from bot.telegram_app import main as start_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_system():
    logger.info("Initializing Database schemas...")
    await init_db()
    logger.info("Database initialized successfully.")

def main():
    import asyncio
    
    # Run the init_system coroutine in an isolated loop just to setup the schema
    asyncio.run(init_system())
    
    # Fix for python-telegram-bot v20+ which requires an event loop in the main thread
    # if it was closed by asyncio.run previously.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Now start the bot in the main thread (python-telegram-bot handles its own event loop under the hood in run_polling)
    logger.info("Starting up Telegram Command Center...")
    start_bot()

if __name__ == "__main__":
    main()
