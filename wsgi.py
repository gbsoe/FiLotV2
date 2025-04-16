#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the Flask web application
"""

import os
import logging
from app import app  # Import the Flask app from app.py

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)

# Initialize or verify database tables
with app.app_context():
    from models import db
    db.create_all()
    logging.info("Database tables created or verified successfully")

# This variable is used by gunicorn to serve the application
application = app

# If run directly, start the development server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)