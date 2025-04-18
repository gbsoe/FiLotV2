#!/bin/bash

# ULTRA SIMPLE SCRIPT TO RUN THE BOT IN PRODUCTION
# This script doesn't need any special configuration
# Just make sure TELEGRAM_TOKEN is set

echo "=========================================="
echo "ULTRA SIMPLE BOT LAUNCHER"
echo "Starting at $(date)"
echo "=========================================="

# Check for token
if [ -z "$TELEGRAM_TOKEN" ] && [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "ERROR: No Telegram token found!"
  echo "Please set TELEGRAM_TOKEN environment variable:"
  echo "export TELEGRAM_TOKEN=your_token_here"
  exit 1
fi

# Create logs directory
mkdir -p logs

# Run the bot
echo "Starting ultra simple bot..."
python ultra_simple_bot.py