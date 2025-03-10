"""
This script defines a Flask web application that generates:
- SQL queries based on user input questions in natural language.
- Executes the generated SQL queries on a PostgreSQL database.
- Descriptions of the database schema in plain language.
- Generates plots based on the executed SQL queries.
- Generate tooltips for the SQL queries.
"""

# LLM
from backend.llm_engine import get_llm

# Routes
from backend.flask_configuration import app

# Flask configuration
from backend.flask_configuration import FLASK_DEBUG, FLASK_RUN_HOST, FLASK_RUN_PORT

# Import routes to register endpoints
import backend.routes

if __name__ == "__main__":

    get_llm()  # Initialize LLM
    app.run(host=FLASK_RUN_HOST, port=FLASK_RUN_PORT, debug=FLASK_DEBUG)
