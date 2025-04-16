#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Flask web application for the Telegram cryptocurrency pool bot
"""

import os
import logging
from datetime import datetime, timedelta

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)

# Configure Flask app
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy with app
db.init_app(app)

# Import models after initializing db
with app.app_context():
    import models
    from monitoring import init_monitoring, get_system_health, health_check_endpoint
    import db_utils
    
    # Drop all tables and recreate them with the updated schema
    db.drop_all()
    db.create_all()
    
    # Create initial bot statistics
    if not models.BotStatistics.query.first():
        stats = models.BotStatistics(
            start_time=datetime.utcnow(),
            command_count=0,
            active_user_count=0,
            subscribed_user_count=0,
            blocked_user_count=0,
            spam_detected_count=0,
            error_count=0,
            uptime_percentage=100.0,
            average_response_time=0.0
        )
        db.session.add(stats)
        db.session.commit()
    
    # Initialize monitoring
    init_monitoring()

# Web application routes

@app.route('/')
def index():
    """Home page."""
    # Get bot statistics
    bot_stats = models.BotStatistics.query.order_by(models.BotStatistics.id.desc()).first()
    
    # Get user counts
    user_count = models.User.query.count()
    subscribed_count = models.User.query.filter_by(is_subscribed=True).count()
    
    return render_template(
        'index.html', 
        stats=bot_stats,
        user_count=user_count,
        subscribed_count=subscribed_count
    )

@app.route('/pools')
def pools():
    """Pool data page."""
    # Get all pools
    pools = db_utils.get_all_pools()
    
    return render_template('pools.html', pools=pools)

@app.route('/users')
def users():
    """User management page."""
    # Get all users
    users = models.User.query.order_by(models.User.last_active.desc()).all()
    
    # Get user counts
    user_count = len(users)
    subscribed_count = models.User.query.filter_by(is_subscribed=True).count()
    
    return render_template(
        'users.html', 
        users=users,
        user_count=user_count,
        subscribed_count=subscribed_count
    )

@app.route('/status')
def status():
    """Bot status page."""
    # Get system health
    health_data = get_system_health()
    
    # Get recent errors
    recent_errors = models.ErrorLog.query.order_by(models.ErrorLog.created_at.desc()).limit(10).all()
    
    # Get statistics over time
    now = datetime.utcnow()
    daily_stats = {
        'dates': [],
        'commands': [],
        'users': []
    }
    
    # Simple statistics for the last 7 days
    for i in range(7):
        day = now - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        next_day = day_start + timedelta(days=1)
        
        # Get command count for the day
        command_count = models.UserQuery.query.filter(
            models.UserQuery.timestamp >= day_start,
            models.UserQuery.timestamp < next_day
        ).count()
        
        # Get active user count for the day
        user_count = models.User.query.filter(
            models.User.last_active >= day_start,
            models.User.last_active < next_day
        ).count()
        
        daily_stats['dates'].insert(0, day_start.strftime('%m/%d'))
        daily_stats['commands'].insert(0, command_count)
        daily_stats['users'].insert(0, user_count)
    
    return render_template(
        'status.html',
        health=health_data,
        errors=recent_errors,
        daily_stats=daily_stats
    )

@app.route('/docs')
def docs():
    """API documentation page."""
    return render_template('docs.html')

@app.route('/api/health')
def api_health():
    """Health check API endpoint."""
    status_code, response = health_check_endpoint()
    return response, status_code

@app.route('/api/stats')
def api_stats():
    """Statistics API endpoint."""
    # Get bot statistics
    bot_stats = models.BotStatistics.query.order_by(models.BotStatistics.id.desc()).first()
    
    if not bot_stats:
        return jsonify({
            'error': 'No statistics available'
        }), 404
    
    # Convert to dictionary
    stats_dict = {
        'command_count': bot_stats.command_count,
        'active_user_count': bot_stats.active_user_count,
        'subscribed_user_count': bot_stats.subscribed_user_count,
        'uptime_percentage': bot_stats.uptime_percentage,
        'average_response_time': bot_stats.average_response_time,
        'error_count': bot_stats.error_count,
        'start_time': bot_stats.start_time.isoformat()
    }
    
    return jsonify(stats_dict)

@app.route('/api/pools')
def api_pools():
    """Pools API endpoint."""
    # Get pools
    pools = db_utils.get_all_pools()
    
    # Convert to dictionary
    pools_dict = [
        {
            'id': pool.id,
            'token_a_symbol': pool.token_a_symbol,
            'token_b_symbol': pool.token_b_symbol,
            'apr_24h': pool.apr_24h,
            'apr_7d': pool.apr_7d,
            'apr_30d': pool.apr_30d,
            'tvl': pool.tvl,
            'token_a_price': pool.token_a_price,
            'token_b_price': pool.token_b_price,
            'fee': pool.fee,
            'last_updated': pool.last_updated.isoformat()
        }
        for pool in pools
    ]
    
    return jsonify(pools_dict)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    # Log the error
    logger.error(f"Server error: {e}")
    
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)