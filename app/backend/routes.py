"""
Contains the routes for the Flask application.
"""

# Python
import json

# Flask
from flask import render_template, request, jsonify, session

# Flask configuration
from app.backend.flask_configuration import MAX_ROWS_DISPLAY, flask_app

# Database
from app.backend.database import get_schema, execute_query, DB_CONFIG

# LLM
from app.backend.llm_engine import (
    generate_sql,
    generate_describe,
    MODEL_NAME,
    create_chart_dictionary,
)

# Bokeh
from bokeh.embed import json_item
from bokeh.resources import CDN

# Third-party
import pandas as pd

# Visualization
from app.backend.visualization.plot_context_selector import (
    build_visualization_context,
    NO_COMPATIBLE_PLOTS_MESSAGE,
)
from app.backend.llm_engine import create_chart_dictionary
from app.backend.visualization.plot_fallback import generate_fallback_plot_config
from app.backend.visualization.generator import get_plot_function


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
    """
    Generate a plot based on the previously executed SQL query result.
    """
    result = session.get("result")
    if not result or "execution" not in result or "data" not in result["execution"]:
        return jsonify({"error": "No data available for plotting"})

    execution = result["execution"]

    # Recreate DataFrame from session data
    try:
        df = pd.DataFrame(execution["data"], columns=execution["columns"])
    except KeyError as e:
        return jsonify({"error": f"Missing data in session: {str(e)}"})

    llm_context = build_visualization_context(execution)

    try:
        # First try LLM-generated config
        plot_config = create_chart_dictionary(llm_context)
    except Exception as e:
        try:
            # Fallback to automated config
            plot_config = generate_fallback_plot_config(execution, llm_context)
        except ValueError as ve:
            if str(ve) == NO_COMPATIBLE_PLOTS_MESSAGE:
                return jsonify({"compatible_plots_error": NO_COMPATIBLE_PLOTS_MESSAGE})
            else:
                return jsonify({"error": str(ve)})

    # Inject the DataFrame into arguments
    plot_config["arguments"]["data"] = df

    try:
        plot = get_plot_function(plot_config)
        return json.dumps(json_item(plot, "chart"))
    except Exception as e:
        return jsonify({"error": str(e)})


@flask_app.route("/generate_tooltip")
def generate_tooltip():
    result = session.get("result")
    sql = result.get("sql", "") if result else ""
    tooltip = f"SQL Length: {len(sql)} characters" if sql else "No SQL available"
    return jsonify({"tooltip": tooltip})
