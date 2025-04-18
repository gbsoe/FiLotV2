#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Flask web application for the Telegram cryptocurrency pool bot
"""

import os
import logging
import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from models import db, User, Pool, BotStatistics, UserQuery, UserActivityLog, ErrorLog

# Load environment variables
load_dotenv()

# Create the Flask application
app = Flask(__name__)

# Configure the Flask application
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Initialize SQLAlchemy with the Flask application
db.init_app(app)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Routes

@app.route("/")
def index():
    """Home page."""
    try:
        # Get basic statistics
        stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
        
        # If no stats exist, create placeholder stats
        if not stats:
            stats = BotStatistics(
                total_users=0,
                active_users_24h=0,
                active_users_7d=0,
                subscribed_users=0,
                total_messages=0,
                total_commands=0,
                response_time_avg=0.0,
                uptime=0
            )
        
        # Get recent user activity
        recent_activity = UserActivityLog.query.order_by(
            UserActivityLog.timestamp.desc()
        ).limit(10).all()
        
        # Get top pools by APR
        top_pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(5).all()
        
        return render_template(
            "index.html",
            stats=stats,
            recent_activity=recent_activity,
            top_pools=top_pools
        )
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template("error.html", error=str(e))

@app.route("/pools")
def pools():
    """Pool data page."""
    try:
        # Get basic pool data directly from the database using text() to properly format SQL
        pool_data = []
        query = text("SELECT id, token_a_symbol, token_b_symbol, apr_24h, apr_7d, tvl, fee FROM pools ORDER BY apr_24h DESC")
        cursor = db.session.execute(query)
        for row in cursor:
            pool_data.append({
                'token_a_symbol': row.token_a_symbol or 'Unknown',
                'token_b_symbol': row.token_b_symbol or 'Unknown',
                'apr_24h': float(row.apr_24h or 0),
                'apr_7d': float(row.apr_7d or 0),
                'tvl': float(row.tvl or 0),
                'fee': float(row.fee or 0) * 100  # Convert to percentage
            })
        
        return render_template("simple_pools.html", pools=pool_data)
    except Exception as e:
        logger.error(f"Error in pools route: {e}")
        return render_template("error.html", error=str(e))

@app.route("/users")
def users():
    """User management page."""
    try:
        # Get user data with direct SQL to avoid ORM issues
        user_data = []
        user_query = text("""
            SELECT 
                id, 
                username, 
                first_name, 
                last_name, 
                is_blocked, 
                is_verified, 
                is_subscribed, 
                created_at, 
                last_active 
            FROM users 
            ORDER BY created_at DESC
        """)
        cursor = db.session.execute(user_query)
        
        for row in cursor:
            # Process each user record safely
            name = ""
            if row.first_name:
                name = row.first_name
                if row.last_name:
                    name += " " + row.last_name
            elif row.username:
                name = row.username
            else:
                name = "Anonymous"
                
            user_data.append({
                'id': row.id,
                'username': row.username,
                'name': name,
                'is_blocked': row.is_blocked,
                'is_verified': row.is_verified,
                'is_subscribed': row.is_subscribed,
                'created_at': row.created_at,
                'last_active': row.last_active
            })
        
        # Get simple counts
        counts = db.session.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_blocked = true THEN 1 ELSE 0 END) as blocked,
                SUM(CASE WHEN is_verified = true THEN 1 ELSE 0 END) as verified,
                SUM(CASE WHEN is_subscribed = true THEN 1 ELSE 0 END) as subscribed
            FROM users
        """).fetchone()
        
        return render_template(
            "simple_users.html",
            users=user_data,
            total_users=counts.total or 0,
            blocked_users=counts.blocked or 0,
            verified_users=counts.verified or 0,
            subscribed_users=counts.subscribed or 0
        )
    except Exception as e:
        logger.error(f"Error in users route: {e}")
        return render_template("error.html", error=str(e))

@app.route("/status")
def status():
    """Bot status page."""
    try:
        # Get latest stats
        stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
        
        # Get recent errors
        recent_errors = ErrorLog.query.order_by(
            ErrorLog.created_at.desc()
        ).limit(20).all()
        
        return render_template(
            "status.html",
            stats=stats,
            recent_errors=recent_errors
        )
    except Exception as e:
        logger.error(f"Error in status route: {e}")
        return render_template("error.html", error=str(e))

@app.route("/docs")
def docs():
    """API documentation page."""
    return render_template("docs.html")

# API Endpoints

@app.route("/api/health")
def api_health():
    """Health check API endpoint."""
    try:
        # Check database connectivity
        db.session.execute("SELECT 1")
        
        # Get uptime
        stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
        uptime = stats.uptime if stats else 0
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "uptime": uptime,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }), 500

@app.route("/api/stats")
def api_stats():
    """Statistics API endpoint."""
    try:
        # Get latest stats
        stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
        
        if not stats:
            return jsonify({"error": "No statistics available"}), 404
        
        return jsonify({
            "total_users": stats.total_users,
            "active_users_24h": stats.active_users_24h,
            "active_users_7d": stats.active_users_7d,
            "subscribed_users": stats.subscribed_users,
            "total_messages": stats.total_messages,
            "total_commands": stats.total_commands,
            "response_time_avg": stats.response_time_avg,
            "uptime": stats.uptime,
            "updated_at": stats.updated_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error in API stats route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/pools")
def api_pools():
    """Pools API endpoint."""
    try:
        # Get all pools
        pools = Pool.query.order_by(Pool.apr_24h.desc()).all()
        
        pool_data = [{
            "id": pool.id,  # Using id directly instead of the property
            "token_a_symbol": pool.token_a_symbol,
            "token_b_symbol": pool.token_b_symbol,
            "token_a_price": pool.token_a_price,
            "token_b_price": pool.token_b_price,
            "apr_24h": pool.apr_24h,
            "apr_7d": pool.apr_7d,
            "apr_30d": pool.apr_30d,
            "tvl": pool.tvl,
            "fee": pool.fee,
            "volume_24h": pool.volume_24h,
            "tx_count_24h": pool.tx_count_24h,
            "updated_at": pool.last_updated.isoformat() if pool.last_updated else None
        } for pool in pools]
        
        return jsonify(pool_data)
    except Exception as e:
        logger.error(f"Error in API pools route: {e}")
        return jsonify({"error": str(e)}), 500

# Error handlers

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template("error.html", error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template("error.html", error="Server error"), 500

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)