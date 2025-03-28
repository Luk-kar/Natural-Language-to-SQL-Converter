"""
Contains the routes for the Flask application.
"""

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
)

# Visualization
from app.backend.visualization.plot_artifact_generator import (
    generate_visualization_artifacts,
)
from app.backend.visualization.plot_fallback import generate_fallback_plot_config
from app.backend.visualization.plot_instruction_prompt_formatter import (
    format_plot_selection_instructions,
    NO_COMPATIBLE_PLOTS_MESSAGE,
)
from app.backend.visualization.plot_context_selector import (
    build_visualization_context,
)


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

                is_chart_possible = False
                try:

                    chart_context = build_visualization_context(execution_result)

                    prompt_context = format_plot_selection_instructions(chart_context)
                    is_chart_possible = prompt_context != NO_COMPATIBLE_PLOTS_MESSAGE

                    if is_chart_possible:
                        generate_fallback_plot_config(execution_result, chart_context)

                except (ValueError, KeyError, TypeError):
                    is_chart_possible = False

                except Exception as e:
                    is_chart_possible = False

                data_valid = (
                    "data" in execution_result
                    and len(execution_result.get("data", [])) > 0
                    and "error" not in execution_result,
                )

                result = {
                    "question": question,
                    "sql": sql,
                    "execution": execution_result,
                    "chart_available": data_valid and is_chart_possible,
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
    execution = result["execution"]

    if not result or "execution" not in result or "data" not in execution:
        return jsonify({"error": "No data available for plotting"})

    return generate_visualization_artifacts(execution)


@flask_app.route("/generate_tooltip")
def generate_tooltip():
    result = session.get("result")
    sql = result.get("sql", "") if result else ""
    tooltip = f"SQL Length: {len(sql)} characters" if sql else "No SQL available"
    return jsonify({"tooltip": tooltip})
