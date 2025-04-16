#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web application for the Telegram cryptocurrency pool bot
"""

import os
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

@app.route('/')
def index():
    """Homepage showing bot information."""
    return render_template('index.html')

@app.route('/status')
def status():
    """API endpoint for bot status."""
    # This would be enhanced to get real data from the bot
    status_data = {
        'bot_active': True,
        'uptime': '0 days, 0 hours, 0 minutes',
        'users': 0,
        'commands_processed': 0,
        'api_status': {
            'raydium': False,
            'ai': False
        }
    }
    return jsonify(status_data)

@app.route('/docs')
def docs():
    """Documentation page."""
    return render_template('docs.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)