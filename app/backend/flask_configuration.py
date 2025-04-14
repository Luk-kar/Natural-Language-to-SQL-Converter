"""
Flask backend configuration file
"""

# Python
import os

# Flask
from flask import Flask

# Configuration - Flask
template_folder = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")
static_folder = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
flask_app = Flask(
    __name__,
    template_folder=template_folder,
    static_folder=static_folder,
)
flask_app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))  # Secret key

MAX_ROWS_DISPLAY = 100

FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
FLASK_RUN_PORT = os.getenv("FLASK_RUN_PORT", "5000")
