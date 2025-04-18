#!/bin/bash

# ULTRA SIMPLE SCRIPT TO LAUNCH THE PRODUCTION BOT
# This script launches the standalone production bot and ensures it stays running

echo "========== PRODUCTION BOT LAUNCHER =========="
echo "Starting at $(date)"
echo "============================================="

# Make sure the bot script is executable
chmod +x production_bot.py

# Create logs directory
mkdir -p logs

# Function to start the bot
start_bot() {
  echo "[$(date)] Starting bot..."
  nohup python3 production_bot.py > logs/bot_output.log 2>&1 &
  BOT_PID=$!
  echo "[$(date)] Bot started with PID: $BOT_PID"
  echo $BOT_PID > bot.pid
}

# Function to check if bot is running
is_bot_running() {
  if [ -f bot.pid ]; then
    PID=$(cat bot.pid)
    if ps -p $PID > /dev/null; then
      return 0
    fi
  fi
  return 1
}

# Start the bot
start_bot

# Monitor the bot and restart if it crashes
echo "[$(date)] Monitoring bot process..."
while true; do
  if ! is_bot_running; then
    echo "[$(date)] Bot process died! Restarting..."
    start_bot
  fi
  
  echo "[$(date)] Bot is running (PID: $(cat bot.pid))"
  
  # Sleep for 30 seconds before checking again
  sleep 30
done