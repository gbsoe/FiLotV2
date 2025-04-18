#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DEBUG BOT LAUNCHER
This script runs the bot and exposes logs via a simple web endpoint
so you can debug production issues remotely.
"""

import os
import sys
import time
import json
import logging
import datetime
import traceback
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque

# Configure logging
os.makedirs("debug_logs", exist_ok=True)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("debug_logs/debug_bot.log")
    ]
)
logger = logging.getLogger("DEBUG_BOT")

# Store logs in memory for web access
LOG_BUFFER = deque(maxlen=1000)  # Store last 1000 log lines
ERROR_BUFFER = deque(maxlen=100)  # Store last 100 error messages

class LogHandler(logging.Handler):
    """Custom log handler that stores logs in memory"""
    def emit(self, record):
        log_entry = self.format(record)
        LOG_BUFFER.append(log_entry)
        if record.levelno >= logging.ERROR:
            ERROR_BUFFER.append(log_entry)

# Add our custom handler
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
memory_handler = LogHandler()
memory_handler.setFormatter(log_formatter)
logging.getLogger().addHandler(memory_handler)

# Log startup
logger.info("Debug bot launcher starting")

# Check environment
token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
if not token:
    logger.error("No TELEGRAM_TOKEN found in environment variables")
    sys.exit(1)

logger.info(f"Found Telegram token starting with {token[:4]}...")

# Simple HTTP server for remote debugging
class DebugHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="text/html"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        
    def do_GET(self):
        if self.path == '/logs':
            self._set_headers(content_type="application/json")
            logs = list(LOG_BUFFER)
            response = {
                'timestamp': datetime.datetime.now().isoformat(),
                'logs': logs,
                'count': len(logs)
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/errors':
            self._set_headers(content_type="application/json")
            errors = list(ERROR_BUFFER)
            response = {
                'timestamp': datetime.datetime.now().isoformat(),
                'errors': errors,
                'count': len(errors)
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/status':
            self._set_headers(content_type="application/json")
            bot_running = process and process.poll() is None
            uptime = int(time.time() - start_time) if process else 0
            response = {
                'timestamp': datetime.datetime.now().isoformat(),
                'bot_running': bot_running,
                'uptime': uptime,
                'restart_count': restart_count,
                'last_restart': last_restart.isoformat() if last_restart else None
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/restart':
            self._set_headers()
            restart_bot()
            self.wfile.write(b"Bot restart initiated")
            
        else:
            self._set_headers()
            self.wfile.write(b"""
            <html>
            <head><title>Bot Debug Interface</title></head>
            <body>
                <h1>Bot Debug Interface</h1>
                <ul>
                    <li><a href="/logs">View Logs</a></li>
                    <li><a href="/errors">View Errors</a></li>
                    <li><a href="/status">Bot Status</a></li>
                    <li><a href="/restart">Restart Bot</a></li>
                </ul>
            </body>
            </html>
            """)

def run_debug_server():
    """Run the debug HTTP server"""
    server_address = ('', 8080)  # Port 8080 for debug server
    httpd = HTTPServer(server_address, DebugHandler)
    logger.info(f"Starting debug server on port {server_address[1]}")
    try:
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Debug server error: {e}")

# Bot management
process = None
start_time = time.time()
restart_count = 0
last_restart = None

def start_bot():
    """Start the bot process"""
    global process, start_time, restart_count, last_restart
    
    if process:
        # Kill existing process if running
        try:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    # Start the bot
    logger.info("Starting bot process")
    try:
        # Use args list to prevent shell injection
        process = subprocess.Popen(
            [sys.executable, "production_bot.py"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            env=os.environ.copy()
        )
        
        start_time = time.time()
        restart_count += 1
        last_restart = datetime.datetime.now()
        
        # Start thread to monitor output
        threading.Thread(target=monitor_output, daemon=True).start()
        
        logger.info(f"Bot started with PID {process.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        logger.error(traceback.format_exc())
        return False

def monitor_output():
    """Monitor the bot's output"""
    for line in iter(process.stdout.readline, ''):
        if line:
            logger.info(f"BOT: {line.strip()}")
    
    # If we get here, the process has ended
    return_code = process.poll()
    logger.warning(f"Bot process exited with code {return_code}")
    
    # Auto-restart if it crashed
    if return_code != 0:
        logger.info("Bot crashed - auto-restarting")
        restart_bot()

def restart_bot():
    """Restart the bot process"""
    logger.info("Restart requested")
    return start_bot()

def main():
    """Main function"""
    # Start the debug server
    threading.Thread(target=run_debug_server, daemon=True).start()
    
    # Start the bot
    if not start_bot():
        logger.error("Failed to start bot")
        sys.exit(1)
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(10)
            # Check if bot is still running
            if process.poll() is not None:
                logger.warning("Bot process died, restarting...")
                start_bot()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        if process:
            process.terminate()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()