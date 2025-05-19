
#!/bin/bash

# FiLot Telegram Bot Production Launcher
# This script properly launches both the web server and bot components

# Make sure logs directory exists
mkdir -p logs

# Kill any existing processes
echo "Checking for existing processes..."
pkill -f "gunicorn --bind 0.0.0.0"
pkill -f "python run_bot.py"
sleep 2

# Start the web server
echo "Starting web server..."
gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --reuse-port wsgi:application >> logs/web_server.log 2>&1 &
WEB_PID=$!
echo "Web server started with PID: $WEB_PID"

# Wait for web server to initialize
sleep 3

# Start the bot in a separate process
echo "Starting Telegram bot..."
python run_bot.py >> logs/bot.log 2>&1 &
BOT_PID=$!
echo "Bot started with PID: $BOT_PID"

# Save PIDs for monitoring
echo "$WEB_PID" > logs/web_server.pid
echo "$BOT_PID" > logs/bot.pid

# Setup simple monitoring
echo "Setting up process monitoring..."
(
  while true; do
    # Check if web server is running
    if ! ps -p $WEB_PID > /dev/null; then
      echo "$(date): Web server crashed, restarting..." >> logs/monitor.log
      gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --reuse-port wsgi:application >> logs/web_server.log 2>&1 &
      WEB_PID=$!
      echo "$WEB_PID" > logs/web_server.pid
    fi
    
    # Check if bot is running
    if ! ps -p $BOT_PID > /dev/null; then
      echo "$(date): Bot crashed, restarting..." >> logs/monitor.log
      python run_bot.py >> logs/bot.log 2>&1 &
      BOT_PID=$!
      echo "$BOT_PID" > logs/bot.pid
    fi
    
    # Keep alive ping to database
    TIMESTAMP=$(date)
    echo "$TIMESTAMP: Monitor heartbeat" >> logs/monitor.log
    
    # Sleep for 30 seconds before checking again
    sleep 30
  done
) &

echo "FiLot is now running! Monitor logs in the logs directory."
echo "Web interface: http://localhost:${PORT:-5000}"
echo "Bot is active on Telegram"
