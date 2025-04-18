# Production Deployment Guide

This guide explains how to deploy and run the Telegram bot and web application in a production environment.

## Important Files

- `main.py` - Main entry point that can run both the Flask app and Telegram bot
- `run_bot_only.py` - Dedicated script for running just the Telegram bot (recommended for production)
- `run_production.sh` - Bash script that runs both the web server and bot with monitoring
- `Procfile` - Configuration for platforms that support Procfile format (like Heroku)

## Environment Variables

The following environment variables must be set:

- `DATABASE_URL` - PostgreSQL database connection string
- `TELEGRAM_TOKEN` or `TELEGRAM_BOT_TOKEN` - Your Telegram bot token

Optional variables:
- `PORT` - Port for the web server (defaults to 5000)
- `SESSION_SECRET` - Secret key for Flask sessions 

## Deployment Options

### Option 1: Using run_production.sh (Recommended)

This script will start both the web server and bot, and monitor them to restart if they crash:

```bash
chmod +x run_production.sh
./run_production.sh
```

### Option 2: Using Procfile

If your platform supports Procfile format:

```
web: gunicorn --bind 0.0.0.0:$PORT --reuse-port --workers 1 wsgi:application
worker: python run_bot_only.py
```

### Option 3: Running Web and Bot Separately

Start the web server:
```bash
gunicorn --bind 0.0.0.0:$PORT --reuse-port wsgi:application
```

Start the bot in a separate process:
```bash
python run_bot_only.py
```

## Troubleshooting

### Bot isn't responding to commands

1. Check if the bot process is running: `ps aux | grep python`
2. Verify the TELEGRAM_TOKEN environment variable is set correctly
3. Check the logs for any errors
4. Try restarting the bot process

### Web server is crashing or timing out

1. The idle timeout is likely shutting down your application
2. Use the run_production.sh script which includes anti-idle mechanisms
3. Make sure DATABASE_URL is correctly set
4. Check database connectivity

### Database errors

1. Verify DATABASE_URL environment variable
2. Check if the database server is accessible 
3. Ensure tables are created using `flask db upgrade` or similar command

## Monitoring

To check the status of the application:

```bash
curl http://localhost:$PORT/health
```

This will return information about the application status, including whether the bot is running.