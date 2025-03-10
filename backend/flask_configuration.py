"""
Flask backend configuration file
"""

# Python
import os

# Flask
from flask import Flask

# Configuration - Flask
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))  # Secret key

MAX_ROWS_DISPLAY = 100

FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
FLASK_RUN_PORT = os.getenv("FLASK_RUN_PORT", "5000")
