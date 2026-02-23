#!/bin/bash

echo "====================================================="
echo "   🚀 STARTING SUPREQUOTE TRACKER PIPELINE 🚀        "
echo "====================================================="

# Activate virtual environment
source venv/bin/activate

# 1. Start the main Telegram Command Center in the background
echo "-> Starting Telegram Bot Background Task..."
python main.py &
BOT_PID=$!

sleep 3

# Display options for the user
echo ""
echo "Bot is online and listening. Check Telegram."
echo ""
echo "To trigger the Live Bet365 Scraper right now, run:"
echo "   source venv/bin/activate && python test_pipeline_e2e.py"
echo ""
echo "Press Ctrl+C to shut down the bot."

# Wait for background process to keep script alive
wait $BOT_PID
