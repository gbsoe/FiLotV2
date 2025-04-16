#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web application for the Telegram cryptocurrency pool bot
"""

import os
import datetime
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure database
db_url = os.environ.get("DATABASE_URL")
if db_url:
    # Make sure to properly format the URL for SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    # Fallback to a SQLite database for development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import models after db initialization to avoid circular imports
with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    """Homepage showing bot information."""
    # Get basic statistics from the database
    bot_stats = models.BotStatistics.query.order_by(models.BotStatistics.id.desc()).first()
    user_count = models.User.query.count()
    subscribed_count = models.User.query.filter_by(is_subscribed=True).count()
    
    # Prepare template context
    context = {
        'user_count': user_count,
        'subscribed_count': subscribed_count,
        'stats': bot_stats
    }
    
    return render_template('index.html', **context)

@app.route('/status')
def status():
    """API endpoint for bot status."""
    # Get data from the database
    bot_stats = models.BotStatistics.query.order_by(models.BotStatistics.id.desc()).first()
    user_count = models.User.query.count()
    
    if bot_stats:
        uptime = datetime.datetime.utcnow() - bot_stats.start_time
        uptime_str = f"{uptime.days} days, {uptime.seconds // 3600} hours, {(uptime.seconds // 60) % 60} minutes"
        command_count = bot_stats.command_count
    else:
        uptime_str = "0 days, 0 hours, 0 minutes"
        command_count = 0
    
    # Prepare status data
    status_data = {
        'bot_active': True,
        'uptime': uptime_str,
        'users': user_count,
        'commands_processed': command_count,
        'api_status': {
            'raydium': True,  # We would normally check this dynamically
            'ai': True        # We would normally check this dynamically
        }
    }
    return jsonify(status_data)

@app.route('/users')
def users():
    """Page showing user list and statistics."""
    users = models.User.query.order_by(models.User.last_active.desc()).limit(50).all()
    user_count = models.User.query.count()
    subscribed_count = models.User.query.filter_by(is_subscribed=True).count()
    
    return render_template('users.html', 
                           users=users, 
                           user_count=user_count,
                           subscribed_count=subscribed_count)

@app.route('/pools')
def pools():
    """Page showing cryptocurrency pool data."""
    pools = models.Pool.query.order_by(models.Pool.apr_24h.desc()).limit(20).all()
    return render_template('pools.html', pools=pools)

@app.route('/docs')
def docs():
    """Documentation page."""
    return render_template('docs.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)