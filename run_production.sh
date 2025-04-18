#!/bin/bash

# This script is for running the Telegram bot in production
# It ensures that both the web app and the bot are running

# Set environment variable to indicate production mode
export PRODUCTION=true

# Make sure we have a telegram token
if [ -z "$TELEGRAM_TOKEN" ] && [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "ERROR: No Telegram token found in environment variables!"
  echo "Please set either TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN"
  exit 1
fi

# Function to start the bot process
start_bot() {
  echo "Starting Telegram bot..."
  python main.py &
  BOT_PID=$!
  echo "Bot started with PID: $BOT_PID"
}

# Function to start the web application
start_web() {
  echo "Starting web application..."
  gunicorn --bind 0.0.0.0:$PORT --reuse-port --workers 1 wsgi:application &
  WEB_PID=$!
  echo "Web app started with PID: $WEB_PID"
}

# Function to check if a process is running
is_running() {
  if ps -p $1 > /dev/null; then
    return 0
  else
    return 1
  fi
}

# Start the processes
start_web
start_bot

# Keep checking that both processes are running
while true; do
  if ! is_running $WEB_PID; then
    echo "Web application crashed! Restarting..."
    start_web
  fi
  
  if ! is_running $BOT_PID; then
    echo "Bot crashed! Restarting..."
    start_bot
  fi
  
  # Log a heartbeat every minute
  echo "Heartbeat: $(date) - Web PID: $WEB_PID, Bot PID: $BOT_PID"
  
  # Sleep for 60 seconds before checking again
  sleep 60
done