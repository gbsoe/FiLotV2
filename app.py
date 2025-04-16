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
        # Get all pools, sorted by APR
        all_pools = Pool.query.order_by(Pool.apr_24h.desc()).all()
        
        return render_template("pools.html", pools=all_pools)
    except Exception as e:
        logger.error(f"Error in pools route: {e}")
        return render_template("error.html", error=str(e))

@app.route("/users")
def users():
    """User management page."""
    try:
        # Get all users
        all_users = User.query.order_by(User.created_at.desc()).all()
        
        # Get counts
        total_users = User.query.count()
        blocked_users = User.query.filter_by(is_blocked=True).count()
        verified_users = User.query.filter_by(is_verified=True).count()
        subscribed_users = User.query.filter_by(is_subscribed=True).count()
        
        # Get recent user queries
        recent_queries = UserQuery.query.order_by(
            UserQuery.timestamp.desc()
        ).limit(20).all()
        
        return render_template(
            "users.html",
            users=all_users,
            total_users=total_users,
            blocked_users=blocked_users,
            verified_users=verified_users,
            subscribed_users=subscribed_users,
            recent_queries=recent_queries
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
            "id": pool.pool_id,
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
            "updated_at": pool.updated_at.isoformat()
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