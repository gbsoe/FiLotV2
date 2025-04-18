# Remote Debugging Guide for Production Server

I understand that the main problem is we need to debug what's happening on your production server without having direct access to the logs. I've created a powerful solution to address this exact problem.

## Remote Debugging Tools

I've created two debugging tools:

### 1. debug_bot.py
This runs your bot with built-in monitoring and exposes a web interface to check logs. This is helpful if your normal bot isn't working.

### 2. debug_remote.py
This is a more comprehensive tool that gives you complete visibility into your production server, including:
- System diagnostics
- Process information
- Connectivity checks
- Log collection
- Command execution

## Installation on Production Server

1. Upload both scripts to your production server:
   ```
   debug_bot.py
   debug_remote.py
   production_bot.py
   ```

2. Install required dependencies:
   ```bash
   pip install psutil requests psycopg2-binary
   ```

3. Make the scripts executable:
   ```bash
   chmod +x debug_bot.py debug_remote.py production_bot.py
   ```

## Using debug_remote.py (Recommended)

1. Start the debug server on your production server:
   ```bash
   python debug_remote.py
   ```
   This starts a web server on port 8080.

2. Access the debug interface from your browser:
   ```
   http://your-server-ip:8080/
   ```

3. From the web interface, you can:
   - View system diagnostics
   - Check connectivity to Telegram API and your database
   - View logs
   - Execute commands like process listing
   - Restart the bot directly

## Using debug_bot.py (Alternative)

If you prefer to run the bot with built-in debugging:

1. Start the debug bot on your production server:
   ```bash
   python debug_bot.py
   ```
   This starts the bot and a debug server on port 8080.

2. Access the debug endpoints from your browser:
   ```
   http://your-server-ip:8080/          # Main page
   http://your-server-ip:8080/logs      # View logs
   http://your-server-ip:8080/errors    # View errors
   http://your-server-ip:8080/status    # Bot status
   http://your-server-ip:8080/restart   # Restart bot
   ```

## Security Note

These debugging tools expose information about your server. They are meant for temporary debugging use. Once you've resolved your issues, stop the debug servers and remove or secure the debug scripts.

## What to Look For

When using these tools, check for:

1. Is the Telegram token correctly loaded?
2. Are there connectivity issues to Telegram API?
3. Are there database connectivity issues?
4. Are there multiple bot instances running?
5. What errors appear in the logs?

With this information, we'll be able to diagnose and fix the production issue much more effectively.