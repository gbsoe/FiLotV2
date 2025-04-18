#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PRODUCTION SERVER REMOTE DEBUG TOOL
This script creates an endpoint that lets you remotely check what's happening
on your production server, view logs, and diagnose issues.

IMPORTANT: This tool should be used for debugging and then removed for security.
"""

import os
import sys
import time
import json
import logging
import datetime
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import StringIO
import socket
import platform
import psutil
import traceback

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("DEBUG_REMOTE")

# Debug port
DEBUG_PORT = 8080

class Diagnostics:
    """Helper class for system diagnostics"""
    
    @staticmethod
    def get_system_info():
        """Get basic system information"""
        try:
            return {
                'hostname': socket.gethostname(),
                'platform': platform.platform(),
                'python_version': sys.version,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_process_info():
        """Get information about running processes"""
        try:
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'status']):
                try:
                    pinfo = proc.info
                    if 'python' in pinfo['name'].lower() or (pinfo['cmdline'] and 'python' in ' '.join(pinfo['cmdline']).lower()):
                        python_processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'cmdline': pinfo['cmdline'],
                            'status': pinfo['status'],
                            'running_time': time.time() - pinfo['create_time'],
                            'memory_info': proc.memory_info()._asdict() if hasattr(proc, 'memory_info') else {}
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return python_processes
        except Exception as e:
            logger.error(f"Error getting process info: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_telegram_token_status():
        """Check if Telegram token is available"""
        token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
        return {
            'has_token': bool(token),
            'token_prefix': token[:4] + '...' if token else None,
            'token_length': len(token) if token else 0
        }
    
    @staticmethod
    def check_connectivity():
        """Check connectivity to important services"""
        results = {}
        
        # Check Telegram API
        try:
            import requests
            telegram_response = requests.get('https://api.telegram.org', timeout=5)
            results['telegram_api'] = {
                'accessible': telegram_response.status_code < 400,
                'status_code': telegram_response.status_code
            }
        except Exception as e:
            results['telegram_api'] = {
                'accessible': False,
                'error': str(e)
            }
        
        # Check database connectivity
        try:
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                # Simple check without importing ORM libraries
                if 'postgres' in db_url:
                    try:
                        import psycopg2
                        conn = psycopg2.connect(db_url)
                        cur = conn.cursor()
                        cur.execute('SELECT 1')
                        cur.close()
                        conn.close()
                        results['database'] = {
                            'accessible': True,
                            'type': 'postgresql'
                        }
                    except Exception as e:
                        results['database'] = {
                            'accessible': False,
                            'type': 'postgresql',
                            'error': str(e)
                        }
                else:
                    results['database'] = {
                        'accessible': 'unknown',
                        'type': 'unknown',
                        'message': 'Unsupported database type'
                    }
            else:
                results['database'] = {
                    'accessible': False,
                    'error': 'DATABASE_URL not set'
                }
        except Exception as e:
            results['database'] = {
                'accessible': False,
                'error': str(e)
            }
            
        return results
    
    @staticmethod
    def get_logs(n=100):
        """Get recent logs"""
        logs = []
        
        # Try to get recent logs from various sources
        try:
            # Look for bot log files
            log_files = [
                'logs/bot_output.log',
                'debug_logs/debug_bot.log',
                'logs/production_bot.log',
                'bot.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        # Get last n lines
                        logs.append({
                            'source': log_file,
                            'lines': list(f.readlines()[-n:])
                        })
        except Exception as e:
            logs.append({
                'source': 'error',
                'lines': [f"Error reading logs: {e}"]
            })
            
        return logs

    @staticmethod
    def execute_command(command):
        """Safely execute a command and return output"""
        try:
            output = subprocess.check_output(
                command, shell=True, stderr=subprocess.STDOUT, timeout=10
            ).decode('utf-8', errors='replace')
            return {'success': True, 'output': output}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': str(e), 'output': e.output.decode('utf-8', errors='replace')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class DebugHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="text/html"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        
    def do_GET(self):
        if self.path == '/api/system':
            # System diagnostics
            self._set_headers(content_type="application/json")
            response = {
                'timestamp': datetime.datetime.now().isoformat(),
                'system': Diagnostics.get_system_info(),
                'processes': Diagnostics.get_process_info(),
                'telegram_token': Diagnostics.get_telegram_token_status()
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/connectivity':
            # Connectivity checks
            self._set_headers(content_type="application/json")
            response = {
                'timestamp': datetime.datetime.now().isoformat(),
                'connectivity': Diagnostics.check_connectivity()
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/logs':
            # Get logs
            self._set_headers(content_type="application/json")
            response = {
                'timestamp': datetime.datetime.now().isoformat(),
                'logs': Diagnostics.get_logs()
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path.startswith('/api/run/'):
            # Run pre-defined commands
            command = self.path[9:]
            allowed_commands = {
                'ps': "ps aux | grep python",
                'env': "env | sort",
                'disk': "df -h",
                'netstat': "netstat -tuln",
                'restart_bot': "pkill -f 'python.*production_bot.py' || true; nohup python production_bot.py > bot.log 2>&1 &"
            }
            
            if command in allowed_commands:
                self._set_headers(content_type="application/json")
                response = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'command': allowed_commands[command],
                    'result': Diagnostics.execute_command(allowed_commands[command])
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid command")
            
        else:
            # Simple HTML interface
            self._set_headers()
            self.wfile.write(b"""
            <html>
            <head>
                <title>Production Server Debug Interface</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                    h1 { color: #333; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .card { background: #f5f5f5; border-radius: 5px; padding: 15px; margin-bottom: 20px; }
                    .button { background: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
                    .button:hover { background: #45a049; }
                    pre { background: #f8f8f8; padding: 10px; border-radius: 5px; overflow: auto; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Production Server Debug Interface</h1>
                    
                    <div class="card">
                        <h2>System Diagnostics</h2>
                        <button class="button" onclick="fetch('/api/system').then(r=>r.json()).then(data=>{document.getElementById('system-output').textContent=JSON.stringify(data, null, 2)})">
                            Run System Diagnostics
                        </button>
                        <pre id="system-output">Click button to run diagnostics...</pre>
                    </div>
                    
                    <div class="card">
                        <h2>Connectivity Checks</h2>
                        <button class="button" onclick="fetch('/api/connectivity').then(r=>r.json()).then(data=>{document.getElementById('connectivity-output').textContent=JSON.stringify(data, null, 2)})">
                            Check Connectivity
                        </button>
                        <pre id="connectivity-output">Click button to check connectivity...</pre>
                    </div>
                    
                    <div class="card">
                        <h2>Logs</h2>
                        <button class="button" onclick="fetch('/api/logs').then(r=>r.json()).then(data=>{document.getElementById('logs-output').textContent=JSON.stringify(data, null, 2)})">
                            View Logs
                        </button>
                        <pre id="logs-output">Click button to view logs...</pre>
                    </div>
                    
                    <div class="card">
                        <h2>Commands</h2>
                        <button class="button" onclick="fetch('/api/run/ps').then(r=>r.json()).then(data=>{document.getElementById('command-output').textContent=JSON.stringify(data, null, 2)})">
                            List Python Processes
                        </button>
                        <button class="button" onclick="fetch('/api/run/env').then(r=>r.json()).then(data=>{document.getElementById('command-output').textContent=JSON.stringify(data, null, 2)})">
                            Show Environment
                        </button>
                        <button class="button" onclick="fetch('/api/run/disk').then(r=>r.json()).then(data=>{document.getElementById('command-output').textContent=JSON.stringify(data, null, 2)})">
                            Check Disk Space
                        </button>
                        <button class="button" onclick="fetch('/api/run/netstat').then(r=>r.json()).then(data=>{document.getElementById('command-output').textContent=JSON.stringify(data, null, 2)})">
                            Check Open Ports
                        </button>
                        <button class="button" onclick="fetch('/api/run/restart_bot').then(r=>r.json()).then(data=>{document.getElementById('command-output').textContent=JSON.stringify(data, null, 2)})">
                            Restart Bot
                        </button>
                        <pre id="command-output">Click a button to run a command...</pre>
                    </div>
                </div>
            </body>
            </html>
            """)

def run_debug_server(port):
    """Run the debug HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DebugHandler)
    logger.info(f"Starting debug server on port {port}")
    httpd.serve_forever()

def main():
    """Main function"""
    logger.info("Remote debug tool starting")
    
    # Check dependencies
    try:
        import psutil
        logger.info("Dependencies loaded successfully")
    except ImportError:
        logger.error("Missing dependencies. Install with: pip install psutil requests psycopg2-binary")
        logger.error("Then try again")
        sys.exit(1)
    
    # Start the server
    try:
        port = int(os.environ.get('DEBUG_PORT', DEBUG_PORT))
        logger.info(f"Starting debug server on port {port}")
        run_debug_server(port)
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as e:
        logger.error(f"Error running debug server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()