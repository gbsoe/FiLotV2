#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the web application
"""

from app import app

# This is needed for Gunicorn to find the app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
