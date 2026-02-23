# 🦾 Trust The Process: Hybrid Value Betting Architecture

A production-grade, end-to-end Value Betting and Superquota extraction pipeline designed for Italian Soft Books (Bet365) and Global Sharp Exchanges (Betfair/Pinnacle). 

This project demonstrates advanced web scraping evasion techniques, real-time mathematical Expected Value (EV) calculation, robust asynchronous database architecture, and a Hybrid Bot-Human operational security model via Telegram.

## 🌟 Key Technical Achievements

*   **Advanced Bot Evasion (DataDome Bypass):** Implemented a custom headless Playwright Chromium instance with targeted stealth arguments and JavaScript `navigator.webdriver` injections to bypass Bet365's aggressive Cloudflare/DataDome protections without relying on expensive residential proxies.
*   **Dynamic DOM Sub-Tree Parsing:** Built a heuristic extraction engine that organically reverse-engineers the live React DOM state of Bet365 to instantly parse complex promotional structures (e.g., separating *"Over 2.5 + Goal"* from *"Fiorentina v Pisa"* natively).
*   **The Odds API Integration (Sharp Book):** Asynchronously fetches real-time "true probabilities" from Pinnacle and Betfair Exchange to act as the mathematical source of truth against the Soft Book's boosted odds.
*   **Quantitative Math Engine:** Employs a custom `Calculator` module to implicitly de-vig (remove the bookmaker's margin) from Exchange lay/back odds to find the *Fair Probability*, calculate the true Expected Value (+EV), and recommend optimal stake sizing using the **Fractional Kelly Criterion**.
*   **Hybrid Bot-Human OpSec (Operational Security):** 
    *   Fully automated scraping and math calculations.
    *   Human-in-the-loop validation via an interactive Telegram Bot.
    *   **Trust Score Mechanics:** The database tracks the user's "Account Health". Taking too many +EV bets lowers the Trust Score. The Telegram Bot proactively warns the user to place `/mug` (Dummy/Cover) bets to reset the algorithm and prevent Bet365 account limitation (profiling).
    *   **Manual Recalibration (`/ricalcola`):** Allows instant Telegram-based EV recalculation for obscure combo Superquotes that lack 1:1 Exchange liquidity.

## 🏗️ Architecture Stack

*   **Language:** Python 3.12+ (Fully Asynchronous `asyncio`)
*   **Ingestion:** `Playwright` (Stealth Chromium), `httpx` (API Requests), `tenacity` (Exponential Backoff)
*   **Math & Matching:** Custom De-Vig Engine, `rapidfuzz` (NLP String Mapping between Bookmakers)
*   **Database:** `SQLAlchemy 2.0` (ORM), `aiosqlite` (Async SQLite for MVP, structured for easy PostgreSQL migration)
*   **Interface:** `python-telegram-bot` (Interactive Webhook/Polling Interface)

## 🚀 How to Run

1.  **Clone & Install:**
    ```bash
    git clone https://github.com/yourusername/trust-the-process.git
    cd trust-the-process
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
    ```

2.  **Environment Variables (`.env`):**
    ```env
    TELEGRAM_TOKEN=your_bot_token
    TELEGRAM_CHAT_ID=your_chat_id
    ODDS_API=your_the_odds_api_key
    USE_SQLITE=true
    ```

3.  **Start the Telegram Operator:**
    ```bash
    # Initializes the DB and starts listening for commands
    python main.py 
    ```

4.  **Run the E2E Extraction Pipeline:**
    ```bash
    # Scrapes Bet365, checks Betfair, calculates EV, and sends Telegram alert
    python test_pipeline_e2e.py
    ```

## 📱 Telegram Commands

*   `/status` - Check current Bankroll and OpSec Trust Score.
*   `/piazzata [importo]` - Confirms the latest Superquota, logs it to DB, updates Bankroll, and lowers Trust Score.
*   `/mug [costo]` - Logs a cover bet (Qualifying Loss) to artificially raise the Trust Score and avoid profiling.
*   `/scartata` - Rejects the current +EV opportunity.
*   `/ricalcola [QuotaBet365] [Lay] [Back]` - Manually forces the Math Engine to recalculate EV if an obscure market isn't queried correctly by the API.

## 🔮 Future Improvements

1. **Docker Compose & PostgreSQL:** Transition from the local `aiosqlite` testing environment to the prepared `asyncpg` PostgreSQL layout via Docker containers on a home Proxmox server for 24/7 uptime.
2. **WebSocket Price Subscriptions:** Move from REST polling on The Odds API to WebSocket streams for millisecond-level Lay odds updates on the Exchange before firing the Telegram alert.
3. **Automated Bet Placement (Betfair):** While Bet365 requires human placement for OpSec, the Betfair Lay (the hedge) could be automated entirely using the Betfair API to guarantee the arbitrage/value instantly upon Telegram `/piazzata` confirmation.