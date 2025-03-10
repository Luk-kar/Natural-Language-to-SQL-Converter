"""
Contains the routes for the Flask application.
"""

# Flask
from flask import render_template, request, jsonify, session

# Database
from app.backend.database import get_schema, execute_query, DB_CONFIG

# LLM
from app.backend.llm_engine import generate_sql, generate_describe, MODEL_NAME

# Flask configuration
from app.backend.flask_configuration import MAX_ROWS_DISPLAY, flask_app


@flask_app.route("/", methods=["GET", "POST"])
def index():
    """
    Starting point for the web application.
    Handles the form submission and generates SQL queries.
    """

    result = None

    if request.method == "POST":
        question = request.form["question"]
        try:
            schema = get_schema()

            if question.strip().upper().startswith("DESCRIBE:"):

                stripped_question = question.strip()[len("DESCRIBE:") :].strip()
                description = generate_describe(schema, stripped_question)
                result = {"question": question, "describe": description}
            else:
                sql = generate_sql(schema, question)
                execution_result = execute_query(sql)

                if "data" in execution_result:
                    execution_result["data"] = execution_result["data"][
                        :MAX_ROWS_DISPLAY
                    ]
                result = {
                    "question": question,
                    "sql": sql,
                    "execution": execution_result,
                }

                session["result"] = result
        except Exception as e:
            result = {"error": str(e)}

    return render_template(
        "index.html",
        result=result,
        model_name=MODEL_NAME,
        db_name=DB_CONFIG["database"],
    )


@flask_app.route("/get_last_sql")
def get_last_sql():
    """Return the last generated SQL from session"""
    result = session.get("result")
    # Extract SQL if result exists and contains 'sql', else default message
    sql = (
        result.get("sql", "No SQL queries generated yet")
        if result
        else "No SQL queries generated yet"
    )
    return jsonify({"sql": sql})


@flask_app.route("/generate_plots")
def generate_plots():
    # TODO

    return {}


@flask_app.route("/generate_tooltip")
def generate_tooltip():
    result = session.get("result")
    sql = result.get("sql", "") if result else ""
    tooltip = f"SQL Length: {len(sql)} characters" if sql else "No SQL available"
    return jsonify({"tooltip": tooltip})
