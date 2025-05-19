#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to create database tables for the Telegram bot
"""

import os
from flask import Flask
from models import db, User, UserQuery, Pool, UserActivityLog, ErrorLog, BotStatistics, SystemBackup, SuspiciousURL

def create_tables():
    """Create all database tables."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Create initial bot statistics
        if BotStatistics.query.count() == 0:
            stats = BotStatistics()
            db.session.add(stats)
            db.session.commit()
            print("Initial bot statistics created!")

if __name__ == "__main__":
    create_tables()